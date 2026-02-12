======================================================================
DCAT-US Gap Report: ESRI WSDL → DCAT-US Crosswalk
======================================================================

Source file type:  ESRI ArcGIS MapServer WSDL
Service name:     EDW_ActivityFactsCommonAttributes_01_MapServer
Endpoint URL:     https://apps.fs.usda.gov/arcx/services/EDW/EDW_ActivityFactsCommonAttributes_01/MapServer
ESRI namespace:   http://www.esri.com/schemas/ArcGIS/3.5.0
Operations found: 55

MAPPED FIELDS (extracted or inferred):
--------------------------------------------------
  [     OK]  title                          ← Derived from service name
  [     OK]  identifier                     ← Service endpoint URL
  [     OK]  distribution.accessURL         ← Service endpoint URL
  [     OK]  distribution.format            ← ESRI SOAP MapServer
  [     OK]  distribution.mediaType         ← application/xml
  [     OK]  publisher.name                 ← Inferred from domain
  [     OK]  keyword                        ← Partial — derived from service name
  [     OK]  accessLevel                    ← Defaulted to 'public'

GAPS (require manual input):
--------------------------------------------------
  [   GAP]  description                    — Not available in WSDL — requires manual input
  [   GAP]  modified                       — No timestamp in WSDL — requires manual input
  [   GAP]  contactPoint                   — Not available in WSDL — requires manual input
  [   GAP]  bureauCode                     — Federal-specific — requires manual input
  [   GAP]  programCode                    — Federal-specific — requires manual input
  [   GAP]  license                        — Not available in WSDL — requires manual input
  [   GAP]  spatial                        — WSDL defines spatial types but no extent values
  [   GAP]  temporal                       — Not available in WSDL — requires manual input
  [   GAP]  theme                          — Not available in WSDL — requires manual input

Summary: 8 fields mapped, 9 gaps requiring manual input.

Fields marked with '[[REQUIRED — provide manually]]'
in the output JSON must be filled in manually.
======================================================================
