#!/usr/bin/env python3
"""
crosswalk.py — Extract metadata from an ESRI ArcGIS MapServer WSDL and
produce a DCAT-US (data.json) catalog record plus a gap report.

Usage:
    python crosswalk.py <wsdl_file> [output_json]

If output_json is omitted, writes to <wsdl_file_stem>_dcat_us.json in the
same directory as the input file.
"""

import json
import os
import re
import sys
import xml.etree.ElementTree as ET

# WSDL / SOAP namespaces
NS = {
    "wsdl": "http://schemas.xmlsoap.org/wsdl/",
    "soap": "http://schemas.xmlsoap.org/wsdl/soap/",
    "xs": "http://www.w3.org/2001/XMLSchema",
}

PLACEHOLDER = "[[REQUIRED — provide manually]]"


def parse_wsdl(path):
    """Parse a WSDL file and extract descriptive metadata."""
    tree = ET.parse(path)
    root = tree.getroot()

    # The root <definitions> may use a default namespace; detect it.
    tag = root.tag
    if tag.startswith("{"):
        default_ns = tag.split("}")[0] + "}"
    else:
        default_ns = ""

    info = {}

    # --- Service name and endpoint ---
    service_el = root.find(f"{default_ns}service")
    if service_el is not None:
        info["service_name"] = service_el.get("name", "")
        port_el = service_el.find(f"{default_ns}port")
        if port_el is not None:
            addr = port_el.find("{http://schemas.xmlsoap.org/wsdl/soap/}address")
            if addr is not None:
                info["endpoint_url"] = addr.get("location", "")

    # --- Target namespace (ESRI schema version) ---
    info["target_namespace"] = root.get("targetNamespace", "")

    # --- Operations from portType ---
    operations = []
    for pt in root.iter(f"{default_ns}portType"):
        for op in pt.findall(f"{default_ns}operation"):
            name = op.get("name")
            if name:
                operations.append(name)
    info["operations"] = sorted(set(operations))

    # --- Infer publisher from endpoint domain ---
    endpoint = info.get("endpoint_url", "")
    if endpoint:
        domain_match = re.search(r"https?://([^/]+)", endpoint)
        if domain_match:
            domain = domain_match.group(1)
            info["domain"] = domain
            if "fs.usda.gov" in domain:
                info["publisher_name"] = "U.S. Forest Service"
                info["publisher_subOrganizationOf"] = "U.S. Department of Agriculture"
            elif "usda.gov" in domain:
                info["publisher_name"] = "U.S. Department of Agriculture"
            else:
                info["publisher_name"] = PLACEHOLDER

    # --- Derive a human-readable title ---
    raw_name = info.get("service_name", "")
    # e.g. "EDW_ActivityFactsCommonAttributes_01_MapServer"
    # Strip trailing _MapServer, replace underscores, clean up
    title = raw_name
    title = re.sub(r"_MapServer$", "", title)
    title = re.sub(r"_(\d+)$", r" \1", title)  # version number
    title = title.replace("_", " ")
    info["title"] = title

    return info


def build_dcat_us(info):
    """Build a DCAT-US data.json structure from extracted WSDL info."""
    endpoint = info.get("endpoint_url", PLACEHOLDER)
    service_name = info.get("service_name", "")

    dataset = {
        "@type": "dcat:Dataset",
        "title": info.get("title", PLACEHOLDER),
        "description": PLACEHOLDER,
        "keyword": [
            "geospatial",
            "map service",
            "ArcGIS",
        ],
        "modified": PLACEHOLDER,
        "publisher": {
            "@type": "org:Organization",
            "name": info.get("publisher_name", PLACEHOLDER),
        },
        "contactPoint": {
            "@type": "vcard:Contact",
            "fn": PLACEHOLDER,
            "hasEmail": PLACEHOLDER,
        },
        "identifier": endpoint,
        "accessLevel": "public",
        "bureauCode": [PLACEHOLDER],
        "programCode": [PLACEHOLDER],
        "license": PLACEHOLDER,
        "spatial": PLACEHOLDER,
        "temporal": PLACEHOLDER,
        "theme": [PLACEHOLDER],
        "distribution": [
            {
                "@type": "dcat:Distribution",
                "accessURL": endpoint,
                "format": "ESRI SOAP MapServer",
                "title": f"{service_name} (SOAP endpoint)",
                "description": (
                    f"SOAP web service with {len(info.get('operations', []))} "
                    f"operations including ExportMapImage, Find, Identify, "
                    f"QueryFeatureData, and others."
                ),
                "mediaType": "application/xml",
            }
        ],
    }

    # Add publisher hierarchy if available
    if info.get("publisher_subOrganizationOf"):
        dataset["publisher"]["subOrganizationOf"] = {
            "@type": "org:Organization",
            "name": info["publisher_subOrganizationOf"],
        }

    # Derive keywords from the service name
    name_parts = info.get("service_name", "").replace("_MapServer", "")
    for part in name_parts.split("_"):
        kw = part.lower()
        if kw and kw not in ("01", "02", "03") and len(kw) > 2:
            dataset["keyword"].append(kw)

    catalog = {
        "conformsTo": "https://project-open-data.cio.gov/v1.1/schema",
        "describedBy": "https://project-open-data.cio.gov/v1.1/schema/catalog.json",
        "@context": "https://project-open-data.cio.gov/v1.1/schema/catalog.jsonld",
        "@type": "dcat:Catalog",
        "dataset": [dataset],
    }

    return catalog


def gap_report(info):
    """Print a gap analysis to stdout."""
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("DCAT-US Gap Report: ESRI WSDL → DCAT-US Crosswalk")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Source file type:  ESRI ArcGIS MapServer WSDL")
    lines.append(f"Service name:     {info.get('service_name', 'N/A')}")
    lines.append(f"Endpoint URL:     {info.get('endpoint_url', 'N/A')}")
    lines.append(f"ESRI namespace:   {info.get('target_namespace', 'N/A')}")
    lines.append(f"Operations found: {len(info.get('operations', []))}")
    lines.append("")

    mapped = [
        ("title", "Derived from service name", True),
        ("identifier", "Service endpoint URL", True),
        ("distribution.accessURL", "Service endpoint URL", True),
        ("distribution.format", "ESRI SOAP MapServer", True),
        ("distribution.mediaType", "application/xml", True),
        ("publisher.name", "Inferred from domain", bool(info.get("publisher_name"))),
        ("keyword", "Partial — derived from service name", True),
        ("accessLevel", "Defaulted to 'public'", True),
    ]

    gaps = [
        ("description", "Not available in WSDL — requires manual input"),
        ("modified", "No timestamp in WSDL — requires manual input"),
        ("contactPoint", "Not available in WSDL — requires manual input"),
        ("bureauCode", "Federal-specific — requires manual input"),
        ("programCode", "Federal-specific — requires manual input"),
        ("license", "Not available in WSDL — requires manual input"),
        ("spatial", "WSDL defines spatial types but no extent values"),
        ("temporal", "Not available in WSDL — requires manual input"),
        ("theme", "Not available in WSDL — requires manual input"),
    ]

    lines.append("MAPPED FIELDS (extracted or inferred):")
    lines.append("-" * 50)
    for field, source, ok in mapped:
        status = "OK" if ok else "PARTIAL"
        lines.append(f"  [{status:>7}]  {field:<30} ← {source}")

    lines.append("")
    lines.append("GAPS (require manual input):")
    lines.append("-" * 50)
    for field, note in gaps:
        lines.append(f"  [   GAP]  {field:<30} — {note}")

    lines.append("")
    lines.append(f"Summary: {len(mapped)} fields mapped, {len(gaps)} gaps requiring manual input.")
    lines.append("")
    lines.append(f"Fields marked with '{PLACEHOLDER}'")
    lines.append("in the output JSON must be filled in manually.")
    lines.append("=" * 70)
    lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <wsdl_file> [output_json]", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.isfile(input_path):
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Determine output path
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        stem = os.path.splitext(os.path.basename(input_path))[0]
        output_dir = os.path.dirname(input_path) or "."
        output_path = os.path.join(output_dir, f"{stem}_dcat_us.json")

    # Parse and extract
    info = parse_wsdl(input_path)

    # Build DCAT-US catalog
    catalog = build_dcat_us(info)

    # Write JSON output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    # Print gap report
    print(gap_report(info))
    print(f"DCAT-US JSON written to: {output_path}")


if __name__ == "__main__":
    main()
