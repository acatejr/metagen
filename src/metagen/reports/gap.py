"""Gap report generator — produces tiered markdown gap analysis reports."""

import json
from datetime import datetime
from pathlib import Path

from metagen.metadata.dcat_us import INSUFFICIENT, PLACEHOLDER

_GAP_FIELDS = [
    ("description", "Not available in WSDL"),
    ("modified", "No timestamp in WSDL"),
    ("contactPoint", "Not available in WSDL"),
    ("bureauCode", "Federal-specific"),
    ("programCode", "Federal-specific"),
    ("license", "Not available in WSDL"),
    ("spatial", "WSDL defines spatial types but no extent values"),
    ("temporal", "Not available in WSDL"),
    ("theme", "Not available in WSDL"),
]

_MAPPED_FIELDS = [
    ("title", "Derived from service name", "OK"),
    ("identifier", "Service endpoint URL", "OK"),
    ("distribution.accessURL", "Service endpoint URL", "OK"),
    ("distribution.format", "ESRI SOAP MapServer", "OK"),
    ("distribution.mediaType", "application/xml", "OK"),
    ("publisher.name", "Inferred from domain", None),  # status resolved at runtime
    ("keyword", "Partial — derived from service name", "OK"),
    ("accessLevel", "Defaulted to 'public'", "OK"),
]


def gap_report(
    info: dict,
    ai_results: dict | None = None,
    ai_metadata: dict | None = None,
    output_dir: Path | str | None = None,
) -> tuple[str, Path]:
    """Build a tiered markdown gap report and write it to output_dir.

    Tiers:
      1. Mapped fields — extracted or inferred from the WSDL
      2. AI-filled fields — suggested by the LLM (if enabled)
      3. Remaining gaps — require manual input

    Args:
        info: metadata dict from readers.wsdl.parse_wsdl()
        ai_results: optional AI-suggested field values
        ai_metadata: optional dict describing the AI run (source, model, error, confidence)
        output_dir: directory to write the report into; defaults to docs/reports/
                    relative to the project root

    Returns:
        (markdown_content, report_path)
    """
    ai = ai_results or {}
    meta = ai_metadata or {}
    confidence = meta.get("confidence", {})

    # Resolve mapped field statuses
    mapped = []
    for field, source, status in _MAPPED_FIELDS:
        if field == "publisher.name":
            status = "OK" if info.get("publisher_name") else "PARTIAL"
        mapped.append((field, source, status))

    # Classify gap fields as AI-filled or still a gap
    ai_filled = []
    remaining_gaps = []

    for field, note in _GAP_FIELDS:
        val = ai.get(field)
        if val is not None and val != INSUFFICIENT:
            if isinstance(val, dict):
                summary = json.dumps(val, ensure_ascii=False)
            elif isinstance(val, list):
                summary = ", ".join(str(v) for v in val)
            else:
                summary = str(val)
            if len(summary) > 80:
                summary = summary[:77] + "..."

            field_conf = confidence.get(field, {})
            level = field_conf.get("level", "N/A").upper()
            reason = field_conf.get("reason", "")
            ai_filled.append((field, summary, level, reason))
        else:
            remaining_gaps.append((field, f"{note} — requires manual input"))

    # AI enrichment status
    source = meta.get("source")
    if source == "ai":
        ai_status = "Enabled"
    elif source == "fallback":
        ai_status = f"Failed: {meta.get('error', 'unknown error')}"
    else:
        ai_status = "Disabled"

    lines = [
        "# DCAT-US Gap Report: ESRI WSDL Crosswalk",
        "",
        "## Source Information",
        "",
        "| Property | Value |",
        "|---|---|",
        f"| **Source file type** | ESRI ArcGIS MapServer WSDL |",
        f"| **Service name** | `{info.get('service_name', 'N/A')}` |",
        f"| **Endpoint URL** | `{info.get('endpoint_url', 'N/A')}` |",
        f"| **ESRI namespace** | `{info.get('target_namespace', 'N/A')}` |",
        f"| **Operations found** | {len(info.get('operations', []))} |",
        f"| **AI enrichment** | {ai_status} |",
    ]

    if source == "ai":
        lines += [
            f"| **AI bot** | {meta.get('bot', 'unknown')} |",
            f"| **AI model** | {meta.get('model', 'unknown')} |",
        ]

    lines += [
        "",
        "## Mapped Fields (extracted from WSDL)",
        "",
        "| Status | DCAT-US Field | Source |",
        "|---|---|---|",
    ]

    for field, source_note, status in mapped:
        lines.append(f"| {status} | `{field}` | {source_note} |")

    if ai_filled:
        lines += [
            "",
            "## AI-Filled Fields (suggested by LLM)",
            "",
            "| Confidence | DCAT-US Field | Value | Justification |",
            "|---|---|---|---|",
        ]
        for field, summary, level, reason in ai_filled:
            lines.append(f"| {level} | `{field}` | {summary} | {reason} |")
        lines += ["", "*AI-suggested values should be reviewed before publication.*"]

    if remaining_gaps:
        lines += [
            "",
            "## Remaining Gaps (require manual input)",
            "",
            "| DCAT-US Field | Notes |",
            "|---|---|",
        ]
        for field, note in remaining_gaps:
            lines.append(f"| `{field}` | {note} |")

    lines += [
        "",
        "## Summary",
        "",
        f"- **{len(mapped)}** fields mapped from the WSDL",
    ]
    if ai_filled:
        lines.append(f"- **{len(ai_filled)}** fields filled by AI")
    if remaining_gaps:
        lines.append(f"- **{len(remaining_gaps)}** gaps still requiring manual input")
    lines += [
        "",
        f"Fields marked with `{PLACEHOLDER}` in the output JSON must be filled in manually.",
        "",
    ]

    body = "\n".join(lines)

    # Prepend Hugo front matter so the report is listed by {{< section >}}
    service_name = info.get("service_name", "Unknown Service")
    iso_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    front_matter = (
        "---\n"
        f'title: "Gap Report: {service_name}"\n'
        f"date: {iso_ts}\n"
        "---\n\n"
    )
    md_content = front_matter + body

    # Resolve output directory
    if output_dir is None:
        # Walk up from this file to find the project root (contains pyproject.toml)
        here = Path(__file__).resolve()
        project_root = here
        for _ in range(10):
            if (project_root / "pyproject.toml").exists():
                break
            project_root = project_root.parent
        output_dir = project_root / "docs" / "reports"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    report_path = output_dir / f"gap_report_{timestamp}.md"
    report_path.write_text(md_content, encoding="utf-8")

    return md_content, report_path
