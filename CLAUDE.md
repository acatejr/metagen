# metagen — CLAUDE.md

## Project Overview

metagen is an AI/LLM-powered CLI tool that automatically generates standards-compliant metadata for geospatial and tabular datasets. See `README.md` for full project description.

**Current status:** Active development. Project structure and CLI scaffold are in place. Key project documents: `README.md`.

## Domain Expertise

When working on this project, apply expertise in:
- Geospatial data formats (shapefiles, geodatabases, GeoJSON, PostGIS, Oracle Spatial, ArcSDE)
- Tabular data formats (CSV, JSON, spreadsheets, SQLite, PostgreSQL, MySQL, Oracle)
- Metadata standards: ISO 19115, FGDC/CSDGM, DCAT, DCAT-US
- ESRI GIS software ecosystem
- Database design and enterprise database connectivity
- Systems architecture and design patterns (adapters, plugins, templating)

## Metadata Standards Context

Output metadata must comply with one or more of these standards:
- **ISO 19115** — International standard for geographic information metadata (XML) — <https://www.iso.org/standard/53798.html>
- **FGDC/CSDGM** — Federal Geographic Data Committee Content Standard for Digital Geospatial Metadata (XML) — <https://www.fgdc.gov/metadata/csdgm-standard>
- **DCAT** — W3C Data Catalog Vocabulary, Version 3 (RDF/JSON-LD) — <https://www.w3.org/TR/vocab-dcat-3/>
- **DCAT-US** — US federal profile of DCAT (JSON) — <https://resources.data.gov/standards/catalog/dcat-us/>

When discussing or implementing metadata generation, consider the full element requirements of the target standard, not just a subset.

### Standards Crosswalk / Gap Analysis

metagen must also support analyzing an existing metadata XML file in one standard and producing a **crosswalk report** to a target standard. This includes:
- Parsing the source XML and identifying which standard and version it conforms to.
- Mapping source elements to their equivalents in the target standard.
- Identifying **gaps** — required target elements that have no corresponding source element or value.
- Identifying **semantic mismatches** — elements that exist in both standards but differ in structure, cardinality, or allowed values.
- Producing an actionable report: what is already covered, what is missing, and what transformations are needed to achieve compliance with the target standard.

### Gap Report Output

Gap reports must be:
- **Formatted as Markdown** with proper headings, tables, and sections.
- **Saved to `docs/reports/`** in the project root directory (create if it does not exist).
- **Named with a timestamp:** `gap_report_YYYY-MM-DD_HHMMSS.md` (e.g., `gap_report_2026-02-12_143022.md`).

## Architecture Guidance

- Use an **adapter/plugin pattern** for data source readers so new formats can be added without modifying core logic.
- Separate concerns: data inspection, LLM-based inference, and metadata serialization should be distinct layers.
- The tool must handle both **file-based sources** (shapefiles, CSV, GeoJSON) and **connection-based sources** (PostgreSQL, Oracle, MySQL) with appropriate credential management.
- Some metadata fields (point of contact, use constraints, distribution info) cannot be inferred from data alone. Design for user-provided defaults or organizational profiles.

## Rules

- **Never read or display the contents of `.env` files.**
- **Respect `.gitignore`** — do not commit or track ignored files.
- **Do not guess.** If you don't know something, say so. Do not fabricate metadata field values, standard requirements, or technical details.
- **Do not create sample/stub code** unless explicitly asked. During planning phases, focus on design, architecture, and documentation.
- **Preserve existing project documents** (`ideas.md`, `tasks.md`, `claude.project.assessment.md`) — edit them only when asked.

## Recording Q&A

When the user says **"record this"** or **"save this Q&A"**, append the most recent question and answer to `docs/claude/qa-log.md` using this format:

```
### Q: <concise question summary>
**Date:** <YYYY-MM-DD>

<answer, preserving key details but written concisely>

---
```

Create the `docs/claude/` directory and `qa-log.md` file if they do not already exist. Do not record unless explicitly asked.

## Saving Notes

When the user says **"save note"** or **"save this note"**, save the most recent question and answer to `docs/notes/` as a markdown file compatible with Hugo. The file name uses the current date and time formatted as `YYYY-MM-DD-HH-MM-SS.md` (e.g. `2026-02-18-20-46-55.md`). The front matter is YAML with:

- `title`: the question
- `date`: ISO 8601 format `YYYY-MM-DDTHH:MM:SS` (e.g. `2026-02-18T20:46:55`) — **not** the filename format
- `draft: true`

The contents of the file use this format:

```
### Q: <concise question summary>
**Date:** <YYYY-MM-DD>

<answer, preserving key details but written concisely>
---
```

Create the `docs/notes` directory if it does not exist.
