---
layout: base.njk
title: Q&A Log
permalink: /qa/
---

# Claude Q&A Log

### Q: How to crosswalk an ESRI WSDL to DCAT-US JSON?
**Date:** 2026-02-12

Created `crosswalk.py`, a stdlib-only Python script that parses an ESRI ArcGIS MapServer WSDL file and produces a DCAT-US (`data.json`) catalog record plus a gap report.

**What the script does:**
1. Parses the WSDL XML with `xml.etree.ElementTree`
2. Extracts service name, endpoint URL, operations list, and ESRI schema namespace
3. Infers publisher from the endpoint domain (e.g., `fs.usda.gov` → U.S. Forest Service / USDA)
4. Builds a DCAT-US JSON structure with extracted values and `[[REQUIRED — provide manually]]` placeholders for fields not available in the WSDL
5. Prints a gap report to stdout and writes JSON to an output file

**Usage:** `python crosswalk.py <wsdl_file> [output_json]`

**8 fields mapped** from the WSDL: `title`, `identifier`, `distribution.accessURL`, `distribution.format`, `distribution.mediaType`, `publisher.name`, `keyword`, `accessLevel`.

**9 gaps** requiring manual input: `description`, `modified`, `contactPoint`, `bureauCode`, `programCode`, `license`, `spatial`, `temporal`, `theme`.

Tested against `data/usfs/EDW_ActivityFactsCommonAttributes_01.xml` (a 6,793-line WSDL with 55 MapServer operations). Output written to `data/usfs/EDW_ActivityFactsCommonAttributes_01_dcat_us.json`.

---
