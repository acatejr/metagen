"""metagen CLI entry point."""
import json
from pathlib import Path

import click


@click.group()
@click.version_option(version="0.1.0", prog_name="metagen")
def main() -> None:
    """AI-powered metadata generation for geospatial and tabular datasets."""


@main.command()
@click.argument("wsdl_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output_json", required=False, default=None, type=click.Path(path_type=Path))
@click.option("--ai", is_flag=True, help="Enable AI gap filling.")
@click.option(
    "--bot",
    type=click.Choice(["verde", "claude"], case_sensitive=False),
    default="verde",
    show_default=True,
    help="AI bot to use (requires --ai).",
)
def crosswalk(wsdl_file: Path, output_json: Path | None, ai: bool, bot: str) -> None:
    """Generate a DCAT-US catalog record and gap report from an ESRI WSDL file.

    WSDL_FILE   Path to the ESRI ArcGIS MapServer WSDL XML file.
    OUTPUT_JSON Path for the output DCAT-US JSON (default: <wsdl_stem>_dcat_us.json).
    """
    from metagen.readers.wsdl import parse_wsdl
    from metagen.readers.rest import wsdl_endpoint_to_rest_url, fetch_rest_metadata, extract_enrichment
    from metagen.metadata.dcat_us import build_dcat_us
    from metagen.reports.gap import gap_report

    if output_json is None:
        output_json = wsdl_file.with_name(f"{wsdl_file.stem}_dcat_us.json")

    # 1. Parse WSDL
    info = parse_wsdl(wsdl_file)

    # 2. Fetch REST metadata (always — provides context for AI and enriches output)
    rest_info = None
    endpoint = info.get("endpoint_url", "")
    rest_url = wsdl_endpoint_to_rest_url(endpoint)
    if rest_url:
        click.echo(f"Fetching REST metadata from: {rest_url}", err=True)
        raw_rest = fetch_rest_metadata(rest_url)
        if raw_rest:
            rest_info = extract_enrichment(raw_rest)
            click.echo("REST metadata retrieved successfully.", err=True)
        else:
            click.echo("Proceeding with WSDL data only (REST unavailable).", err=True)

    # 3. AI gap filling (opt-in via --ai)
    ai_results: dict = {}
    ai_metadata: dict = {"source": "none"}
    if ai:
        from metagen.llm.gap_filler import ai_gap_fill
        click.echo("Running AI gap-filling...", err=True)
        ai_results, ai_metadata = ai_gap_fill(info, rest_info, bot=bot)
        if ai_metadata.get("source") == "ai":
            filled = sum(1 for v in ai_results.values() if v is not None)
            click.echo(f"AI suggested values for {filled} of 9 gap fields.", err=True)
        else:
            click.echo(f"AI gap-filling unavailable: {ai_metadata.get('error', 'unknown')}", err=True)

    # 4. Build DCAT-US catalog
    catalog = build_dcat_us(info, ai_results=ai_results)

    # 5. Write JSON output
    output_json.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")

    # 6. Generate and save gap report
    md_content, report_path = gap_report(info, ai_results=ai_results, ai_metadata=ai_metadata)
    click.echo(md_content)
    click.echo(f"Gap report written to:   {report_path}")
    click.echo(f"DCAT-US JSON written to: {output_json}")


if __name__ == "__main__":
    main()
