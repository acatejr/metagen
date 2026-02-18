"""metagen CLI entry point."""
import click


@click.group()
@click.version_option(version="0.1.0", prog_name="metagen")
def main() -> None:
    """AI-powered metadata generation for geospatial and tabular datasets."""


if __name__ == "__main__":
    main()
