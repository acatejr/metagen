# metagen

An AI-powered tool that automatically generates standards-compliant metadata for tabular and geospatial data sets.

## Overview

Creating metadata for geospatial and tabular data is often tedious and time-consuming. **metagen** uses AI/LLM capabilities to inspect data sources and produce well-structured metadata records that comply with established standards.


**THIS WORK IS PROOF OF CONCEPT AND IN PLANNING-DEVELOPMENT AND IDEA DEVELOPMENT!!!**

**NO APP EXISTS YET!!**

## Supported Metadata Standards

metagen can generate metadata conforming to:

- **ISO 19115** -- International standard for geographic information metadata
- **FGDC CSDGM** -- Federal Geographic Data Committee Content Standard for Digital Geospatial Metadata
- **DCAT / DCAT-US** -- Data Catalog Vocabulary (and its US federal profile)

## Standards Crosswalk / Gap Analysis

metagen can also analyze an existing metadata XML file and produce a crosswalk report to a different target standard. Given a source file (e.g., FGDC/CSDGM XML), the tool will:

- Detect the source standard and version
- Map elements to their equivalents in the target standard
- Identify gaps -- required target elements with no corresponding source value
- Flag semantic mismatches -- elements that differ in structure, cardinality, or allowed values
- Produce an actionable report of what is covered, what is missing, and what transformations are needed

## Supported Data Sources

### Geospatial

| Source | Format / Extension |
|---|---|
| Shapefiles | `.shp` |
| Personal Geodatabases | `.mdb` |
| GeoJSON | `.geojson` / `.json` |
| PostgreSQL + PostGIS | via connection string |
| Oracle Spatial | via connection string |
| ArcSDE | enterprise geodatabase bridge |

### Tabular

| Source | Format / Extension |
|---|---|
| CSV | `.csv` |
| Spreadsheets | `.xlsx`, `.xls`, `.ods` |
| JSON | `.json` |
| SQLite | `.sqlite`, `.db` |
| PostgreSQL | via connection string |
| MySQL | via connection string |
| Oracle | via connection string |

## Getting Started

*This project is under active development. Setup and usage instructions will be added as the tool matures.*

## Contributing

Contributions, ideas, and feedback are welcome. Please open an issue to start a discussion before submitting a pull request.

## License

*License information to be determined.*
