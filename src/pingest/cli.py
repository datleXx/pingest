import typer

from pingest import __version__

app = typer.Typer(
    name="pingest",
    help="Pingest — a small command-line data-ingestion tool.",
    no_args_is_help=True,
)


def _version_callback(show: bool) -> None:
    if show:
        typer.echo(f"pingest {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        help="Show the version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Pingest top-level CLI. Subcommands (ingest-api, ingest-file) come later."""
