"""REST reader — fetch and normalize metadata from ArcGIS REST endpoints.

Converts ESRI WSDL SOAP endpoint URLs to their REST equivalents and
extracts metadata useful for gap-filling (spatial extent, service
description, keywords, layer info, etc.).
"""

import re
import sys

import requests


def wsdl_endpoint_to_rest_url(wsdl_endpoint: str) -> str:
    """Convert a WSDL SOAP endpoint URL to its ArcGIS REST equivalent.

    Example:
        Input:  https://apps.fs.usda.gov/arcx/services/EDW/EDW_Foo/MapServer
        Output: https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_Foo/MapServer?f=json
    """
    if not wsdl_endpoint:
        return ""

    # Standard ArcGIS Server pattern: insert /rest/ before /services/
    rest_url = re.sub(r"/services/", "/rest/services/", wsdl_endpoint, count=1)

    if rest_url == wsdl_endpoint:
        print(
            f"Warning: Could not convert WSDL endpoint to REST URL: {wsdl_endpoint}",
            file=sys.stderr,
        )
        return ""

    return f"{rest_url}?f=json"


def fetch_rest_metadata(rest_url: str, timeout: int = 30) -> dict | None:
    """Fetch the ArcGIS REST endpoint JSON.

    Returns the parsed dict on success, None on any failure.
    """
    if not rest_url:
        return None

    try:
        resp = requests.get(rest_url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        print(
            f"Warning: REST endpoint timed out after {timeout}s: {rest_url}",
            file=sys.stderr,
        )
    except requests.exceptions.RequestException as e:
        print(
            f"Warning: Could not fetch REST metadata: {e}",
            file=sys.stderr,
        )
    except ValueError:
        print(
            "Warning: REST endpoint returned invalid JSON.",
            file=sys.stderr,
        )
    return None


def extract_enrichment(rest_data: dict) -> dict:
    """Extract metadata relevant to gap-filling from raw ArcGIS REST JSON.

    Returns a dict with normalized keys. Missing fields default to None
    or empty lists.
    """
    doc_info = rest_data.get("documentInfo") or {}

    # Parse keywords string into a list
    raw_keywords = doc_info.get("Keywords", "")
    if isinstance(raw_keywords, str) and raw_keywords.strip():
        keywords = [k.strip() for k in raw_keywords.split(",") if k.strip()]
    else:
        keywords = []

    # Extract layer summaries
    layers = [
        {
            "id": layer.get("id"),
            "name": layer.get("name", ""),
            "type": layer.get("type", ""),
            "description": layer.get("description", ""),
        }
        for layer in (rest_data.get("layers") or [])
    ]

    return {
        "service_description": rest_data.get("serviceDescription") or None,
        "description": rest_data.get("description") or None,
        "document_title": doc_info.get("Title") or None,
        "document_subject": doc_info.get("Subject") or None,
        "document_author": doc_info.get("Author") or None,
        "document_keywords": keywords,
        "copyright_text": rest_data.get("copyrightText") or None,
        "spatial_reference_wkid": (rest_data.get("spatialReference") or {}).get("wkid"),
        "full_extent": rest_data.get("fullExtent"),
        "initial_extent": rest_data.get("initialExtent"),
        "layers": layers,
        "capabilities": rest_data.get("capabilities") or None,
    }
