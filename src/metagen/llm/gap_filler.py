"""LLM gap filler — uses an AI model to suggest values for metadata fields that
cannot be inferred from the source data alone."""

import json
import os
import re
import sys

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"

DCAT_SYSTEM_PROMPT = """\
You are a federal geospatial metadata specialist. Your task is to suggest \
DCAT-US metadata field values for an ArcGIS MapServer service based on \
evidence from the service's WSDL definition and REST endpoint metadata.

RULES:
- Only provide values that are supported by the evidence provided.
- If you cannot determine a value from the available data, set it to \
"INSUFFICIENT_EVIDENCE" — do NOT guess or fabricate.
- For spatial extent, use the format "xmin,ymin,xmax,ymax" in WGS84 \
(EPSG:4326). If the source uses a projected CRS, note the original \
and provide the WGS84 equivalent if you can determine it. NAD83 \
(EPSG:4269) coordinates are acceptable as-is since they are \
essentially equivalent to WGS84 for metadata purposes.
- For temporal, use ISO 8601 interval format: "YYYY-MM-DD/YYYY-MM-DD" \
or "R/YYYY-MM-DD/P1Y" for ongoing datasets.
- For bureauCode, use the official OMB bureau codes (e.g., "005:96" \
for USDA Forest Service).
- For programCode, use the official OMB program codes.
- For license, suggest the appropriate federal open data license URL.
- For theme, use ISO 19115 topic categories.
- Return ONLY valid JSON matching the schema described. No markdown \
fences, no commentary — just the JSON object.
- For missing values make suggestions on where to find the information \
in the WSDL or REST metadata, but do not fabricate values. Save the \
recommendations in the report in a "suggestions" section.
"""

_EXPECTED_FIELDS = {
    "description", "modified", "contactPoint", "bureauCode",
    "programCode", "license", "spatial", "temporal", "theme",
}

_BOT_MODEL_ENV = {
    "verde": "VERDE_MODEL",
    "claude": "METAGEN_MODEL",
}


def build_gap_fill_prompt(wsdl_info: dict, rest_info: dict | None) -> str:
    """Construct the user message for the LLM API call."""
    rest_section = (
        json.dumps(rest_info, indent=2, default=str)
        if rest_info
        else "REST endpoint metadata was unavailable."
    )

    return f"""\
## Source Data: ESRI ArcGIS MapServer WSDL

### WSDL Extracted Information
{json.dumps(wsdl_info, indent=2, default=str)}

### ArcGIS REST Endpoint Metadata
{rest_section}

## Required Output

Provide a JSON object with these exact keys. Each value must conform to \
the DCAT-US v1.1 schema (https://project-open-data.cio.gov/v1.1/schema):

{{
  "description": "string — A human-readable description of the dataset",
  "modified": "string — ISO 8601 date (YYYY-MM-DD) when last updated",
  "contactPoint": {{
    "fn": "string — Contact person or organization name",
    "hasEmail": "string — mailto: URI for the contact email"
  }},
  "bureauCode": ["string — OMB bureau code in NNN:NN format"],
  "programCode": ["string — OMB program code in NNN:NNN format"],
  "license": "string — URL for the license",
  "spatial": "string — Geographic extent as xmin,ymin,xmax,ymax in WGS84",
  "temporal": "string — Temporal coverage in ISO 8601 interval format",
  "theme": ["string — ISO 19115 topic categories"]
}}

For each field, also provide a confidence level and brief justification \
in a separate "confidence" key:

{{
  "confidence": {{
    "description": {{"level": "high|medium|low", "reason": "..."}},
    "modified": {{"level": "high|medium|low", "reason": "..."}},
    ...
  }}
}}

Return a single JSON object containing both the field values and the \
confidence object. No markdown fences or extra text.\
"""


def parse_ai_response(response_text: str) -> tuple[dict, dict]:
    """Parse the LLM's JSON response into field values and confidence.

    Strips markdown code fences if present. Warns on missing expected fields.

    Returns:
        (values_dict, confidence_dict). On parse failure returns ({}, {}).
    """
    text = response_text.strip()

    # Strip markdown code fences if the model included them anyway
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse AI response as JSON: {e}", file=sys.stderr)
        return {}, {}

    if not isinstance(data, dict):
        print("Warning: AI response is not a JSON object.", file=sys.stderr)
        return {}, {}

    confidence = data.pop("confidence", {})
    values = {k: v for k, v in data.items() if k in _EXPECTED_FIELDS}

    missing = _EXPECTED_FIELDS - set(values.keys())
    if missing:
        print(
            f"Warning: AI response missing fields: {', '.join(sorted(missing))}",
            file=sys.stderr,
        )

    return values, confidence


def _get_anthropic_client():
    """Initialize and return an Anthropic client, or None if unavailable."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "Warning: ANTHROPIC_API_KEY not set. AI gap-filling disabled.",
            file=sys.stderr,
        )
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=api_key)
    except Exception as e:
        print(f"Warning: Could not initialize Anthropic client: {e}", file=sys.stderr)
        return None


def ai_gap_fill(
    wsdl_info: dict,
    rest_info: dict | None = None,
    bot: str = "verde",
) -> tuple[dict, dict]:
    """Suggest values for DCAT-US gap fields using the selected bot.

    Args:
        wsdl_info: metadata dict from readers.wsdl.parse_wsdl()
        rest_info: optional enrichment dict from readers.rest.extract_enrichment()
        bot: which bot to use — "verde" (default) or "claude"

    Returns:
        (ai_results, ai_metadata) where:
          ai_results  — dict mapping DCAT-US field names to suggested values
          ai_metadata — dict with keys: source, bot, model, error, confidence
    """
    user_message = build_gap_fill_prompt(wsdl_info, rest_info)

    if bot == "verde":
        from metagen.llm.bots import VerdeBot
        try:
            response = VerdeBot().chat([
                ("system", DCAT_SYSTEM_PROMPT),
                ("human", user_message),
            ])
            response_text = response.content
        except Exception as e:
            return {}, {"source": "fallback", "bot": bot, "error": str(e)}
        model_name = os.environ.get("VERDE_MODEL", "unknown")

    else:  # claude
        client = _get_anthropic_client()
        if client is None:
            return {}, {"source": "fallback", "bot": bot, "error": "No API key"}
        model_name = os.environ.get("METAGEN_MODEL", DEFAULT_MODEL)
        try:
            response = client.messages.create(
                model=model_name,
                max_tokens=2048,
                system=DCAT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            response_text = response.content[0].text
        except Exception as e:
            return {}, {"source": "fallback", "bot": bot, "error": str(e)}

    values, confidence = parse_ai_response(response_text)

    if not values:
        return {}, {"source": "fallback", "bot": bot, "error": "Failed to parse AI response"}

    return values, {
        "source": "ai",
        "bot": bot,
        "model": model_name,
        "confidence": confidence,
    }
