---
layout: base.njk
title: metagen — Project Blog
---

# metagen

An AI/LLM-powered CLI tool that automatically generates standards-compliant metadata for geospatial and tabular datasets.

## Recent Reports

{% for report in collections.reports %}
- [{{ report.data.title }}]({{ report.url }})
{% endfor %}
