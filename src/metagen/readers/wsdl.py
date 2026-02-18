"""WSDL reader — extracts descriptive metadata from ESRI ArcGIS MapServer WSDL files."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

PLACEHOLDER = "[[REQUIRED — provide manually]]"


def parse_wsdl(path: str | Path) -> dict:
    """Parse a WSDL file and return extracted metadata.

    Returns a dict with keys:
      service_name, endpoint_url, target_namespace, operations,
      domain, publisher_name, publisher_subOrganizationOf (optional), title
    """
    tree = ET.parse(path)
    root = tree.getroot()

    # Detect default namespace from root tag, e.g. "{http://...}definitions"
    tag = root.tag
    default_ns = tag.split("}")[0] + "}" if tag.startswith("{") else ""

    info: dict = {}

    # Service name and SOAP endpoint URL
    service_el = root.find(f"{default_ns}service")
    if service_el is not None:
        info["service_name"] = service_el.get("name", "")
        port_el = service_el.find(f"{default_ns}port")
        if port_el is not None:
            addr = port_el.find("{http://schemas.xmlsoap.org/wsdl/soap/}address")
            if addr is not None:
                info["endpoint_url"] = addr.get("location", "")

    # Target namespace (indicates ESRI schema version)
    info["target_namespace"] = root.get("targetNamespace", "")

    # Operations from portType
    operations: list[str] = []
    for pt in root.iter(f"{default_ns}portType"):
        for op in pt.findall(f"{default_ns}operation"):
            name = op.get("name")
            if name:
                operations.append(name)
    info["operations"] = sorted(set(operations))

    # Infer publisher from endpoint domain
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

    # Derive a human-readable title from the service name
    # e.g. "EDW_ActivityFactsCommonAttributes_01_MapServer" → "EDW ActivityFactsCommonAttributes 1"
    raw_name = info.get("service_name", "")
    title = re.sub(r"_MapServer$", "", raw_name)
    title = re.sub(r"_(\d+)$", r" \1", title)
    title = title.replace("_", " ")
    info["title"] = title

    return info
