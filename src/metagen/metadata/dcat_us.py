"""DCAT-US serializer — builds a DCAT-US data.json catalog record from extracted metadata."""

import json

PLACEHOLDER = "[[REQUIRED — provide manually]]"
INSUFFICIENT = "INSUFFICIENT_EVIDENCE"


def _resolve_ai(ai_results: dict | None, field_name: str, default=None):
    """Return the AI-suggested value if usable, otherwise the placeholder or default."""
    if ai_results is None:
        return default if default is not None else PLACEHOLDER
    val = ai_results.get(field_name)
    if val is None or val == INSUFFICIENT:
        return default if default is not None else PLACEHOLDER
    return val


def build_dcat_us(info: dict, ai_results: dict | None = None) -> dict:
    """Build a DCAT-US data.json catalog record from extracted WSDL info.

    Args:
        info: metadata dict returned by readers.wsdl.parse_wsdl()
        ai_results: optional dict of AI-suggested gap field values

    Returns:
        A dict conforming to the DCAT-US v1.1 catalog schema.
    """
    endpoint = info.get("endpoint_url", PLACEHOLDER)
    service_name = info.get("service_name", "")

    ai_contact = (ai_results or {}).get("contactPoint", {})
    if isinstance(ai_contact, dict):
        contact_fn = ai_contact.get("fn", PLACEHOLDER)
        contact_email = ai_contact.get("hasEmail", PLACEHOLDER)
        if contact_fn == INSUFFICIENT:
            contact_fn = PLACEHOLDER
        if contact_email == INSUFFICIENT:
            contact_email = PLACEHOLDER
    else:
        contact_fn = PLACEHOLDER
        contact_email = PLACEHOLDER

    # Base keyword list — supplemented from the service name below
    keywords = ["geospatial", "map service", "ArcGIS"]
    name_parts = service_name.replace("_MapServer", "").split("_")
    for part in name_parts:
        kw = part.lower()
        if kw and kw not in ("01", "02", "03") and len(kw) > 2:
            keywords.append(kw)

    dataset = {
        "@type": "dcat:Dataset",
        "title": info.get("title", PLACEHOLDER),
        "description": _resolve_ai(ai_results, "description"),
        "keyword": keywords,
        "modified": _resolve_ai(ai_results, "modified"),
        "publisher": {
            "@type": "org:Organization",
            "name": info.get("publisher_name", PLACEHOLDER),
        },
        "contactPoint": {
            "@type": "vcard:Contact",
            "fn": contact_fn,
            "hasEmail": contact_email,
        },
        "identifier": endpoint,
        "accessLevel": "public",
        "bureauCode": _resolve_ai(ai_results, "bureauCode", [PLACEHOLDER]),
        "programCode": _resolve_ai(ai_results, "programCode", [PLACEHOLDER]),
        "license": _resolve_ai(ai_results, "license"),
        "spatial": _resolve_ai(ai_results, "spatial"),
        "temporal": _resolve_ai(ai_results, "temporal"),
        "theme": _resolve_ai(ai_results, "theme", [PLACEHOLDER]),
        "distribution": [
            {
                "@type": "dcat:Distribution",
                "accessURL": endpoint,
                "format": "ESRI SOAP MapServer",
                "title": f"{service_name} (SOAP endpoint)",
                "description": (
                    f"SOAP web service with {len(info.get('operations', []))} "
                    "operations including ExportMapImage, Find, Identify, "
                    "QueryFeatureData, and others."
                ),
                "mediaType": "application/xml",
            }
        ],
    }

    if info.get("publisher_subOrganizationOf"):
        dataset["publisher"]["subOrganizationOf"] = {
            "@type": "org:Organization",
            "name": info["publisher_subOrganizationOf"],
        }

    catalog = {
        "conformsTo": "https://project-open-data.cio.gov/v1.1/schema",
        "describedBy": "https://project-open-data.cio.gov/v1.1/schema/catalog.json",
        "@context": "https://project-open-data.cio.gov/v1.1/schema/catalog.jsonld",
        "@type": "dcat:Catalog",
        "dataset": [dataset],
    }

    return catalog
