## Project Assessment: metagen

### Core Goal

**metagen** aims to be an AI/LLM-powered tool that **automatically generates standards-compliant metadata** for geospatial and tabular datasets. The central problem it solves: metadata authoring is tedious, manual, and often skipped -- leaving datasets undiscoverable and non-compliant.

### What the Tool Should Do

1. **Inspect a data source** (file or database connection) and extract structural and semantic information -- column names, data types, spatial extent, temporal coverage, coordinate reference systems, etc.
2. **Use AI/LLM reasoning** to infer higher-level descriptors -- purpose, abstract, keywords, lineage -- that go beyond what raw schema inspection provides.
3. **Emit metadata records** in one or more standard formats: ISO 19115, FGDC/CSDGM, DCAT, or DCAT-US.

### Current State

The project is in the **planning/ideation phase**. There is no code yet -- only documentation:
- `CLAUDE.md` -- project instructions and constraints
- `README.md` -- polished overview of supported sources and standards
- `tasks.md` -- the original task description
- `ideas.md` -- a thoughtful exploration of whether the tool could make metadata standards obsolete

### Key Design Challenges Ahead

1. **Data source abstraction** -- The input matrix is wide (shapefiles, geodatabases, PostGIS, Oracle Spatial, ArcSDE, CSV, JSON, spreadsheets, SQLite, MySQL). Each requires a different reader/driver. A plugin or adapter pattern will be important.
2. **Schema-to-semantics gap** -- Extracting column names is easy; inferring that a column named `AADT` means "Annual Average Daily Traffic" requires AI. This is where the LLM adds value.
3. **Standards output** -- ISO 19115, FGDC/CSDGM, and DCAT have very different structures (XML vs. RDF/JSON-LD). Templating or serialization will need to handle each.
4. **Enterprise database connectivity** -- Connecting to PostgreSQL/PostGIS or Oracle Spatial requires connection strings, credentials, and potentially ArcSDE middleware. Security and configuration UX matter here.
5. **Metadata completeness** -- Some required metadata fields (point of contact, distribution info, use constraints) can't be inferred from data alone. The tool will need a way to accept user-provided context or organizational defaults.

### Summary

The project has a clear, well-scoped goal with real practical value. The vision is sound -- reduce the metadata burden so datasets actually get documented. The next step is moving from planning into architecture and implementation: choosing a language/framework, designing the data source adapter layer, defining the LLM prompting strategy, and building a first working prototype against the simplest input (e.g., a CSV or shapefile) and one output standard.
