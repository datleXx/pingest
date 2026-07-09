import typer

from pingest import __version__
from pingest.config import settings
from pingest.logging_helper.core import get_logger
from pingest.models.soccer import FlatMatch, FlatScorer, FlatStanding
from pingest.sink import write_records
from pingest.sources.fetch import fetch_async, fetch_sequential, fetch_threaded
from pingest.sources.soccer_api import SoccerApiClient

logger = get_logger(__name__)

app = typer.Typer(
    name="pingest",
    help="Pingest — soccer data ingestion CLI.",
    no_args_is_help=False,
    invoke_without_command=True,
)


def _version_callback(show: bool) -> None:
    if show:
        typer.echo(f"pingest {__version__}")
        raise typer.Exit()


def _make_client() -> SoccerApiClient:
    return SoccerApiClient(settings.football_api_key, settings.api_rate_limit)


def _fetch(client: SoccerApiClient, mode: str, tasks: list[tuple[str, dict]]) -> list:
    if mode == "threaded":
        return fetch_threaded(client, tasks)
    if mode == "async":
        return fetch_async(client, tasks)
    return fetch_sequential(client, tasks)


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        help="Show the version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Pingest — soccer data ingestion CLI."""
    if ctx.invoked_subcommand is None:
        from pingest.interactive import start

        start()


@app.command(name="ingest-matches")
def ingest_matches(
    competition: str = typer.Option(..., help="Competition code e.g. PL, CL"),
    season: int = typer.Option(..., help="Season start year e.g. 2024"),
    status: str = typer.Option(None, help="FINISHED, SCHEDULED, LIVE"),
    mode: str = typer.Option("sequential", help="sequential, threaded, async"),
    fmt: str = typer.Option("parquet", help="Output format: parquet, csv"),
    output: str = typer.Option(None, help="Output directory"),
):
    out = output or settings.output_dir
    client = _make_client()
    tasks = [("get_competition_matches", {"competition": competition, "season": season, "status": status})]
    matches = _fetch(client, mode, tasks)[0]
    records = [FlatMatch.from_api(m).model_dump() for m in matches]
    write_records(records, out, fmt=fmt, partition_cols=["match_date"], batch_size=settings.batch_size)
    typer.echo(f"Wrote {len(records)} matches for {competition} {season} → {out}/")


@app.command(name="ingest-standings")
def ingest_standings(
    competition: str = typer.Option(..., help="Competition code e.g. PL"),
    season: int = typer.Option(..., help="Season start year e.g. 2024"),
    fmt: str = typer.Option("parquet", help="Output format: parquet, csv"),
    output: str = typer.Option(None, help="Output directory"),
):
    out = output or settings.output_dir
    client = _make_client()
    standings = client.get_standings(competition, season=season)
    records = []
    for group in standings:
        for row in group["table"]:
            records.append(FlatStanding.from_api(
                row,
                competition_code=competition,
                season_start_year=season,
                stage=group["stage"],
                type=group["type"],
            ).model_dump())
    write_records(records, out, fmt=fmt, partition_cols=["competition_code"], batch_size=settings.batch_size)
    typer.echo(f"Wrote {len(records)} standing rows for {competition} {season} → {out}/")


@app.command(name="ingest-scorers")
def ingest_scorers(
    competition: str = typer.Option(..., help="Competition code e.g. PL"),
    season: int = typer.Option(..., help="Season start year e.g. 2024"),
    fmt: str = typer.Option("parquet", help="Output format: parquet, csv"),
    output: str = typer.Option(None, help="Output directory"),
):
    out = output or settings.output_dir
    client = _make_client()
    scorers = client.get_scorers(competition, season=season)
    records = [
        FlatScorer.from_api(s, competition_code=competition, season_start_year=season).model_dump()
        for s in scorers
    ]
    write_records(records, out, fmt=fmt, partition_cols=["competition_code"], batch_size=settings.batch_size)
    typer.echo(f"Wrote {len(records)} scorers for {competition} {season} → {out}/")


@app.command(name="ingest-team")
def ingest_team(
    team_id: int = typer.Option(..., help="Team numeric ID e.g. 86"),
    season: int = typer.Option(None, help="Season start year e.g. 2024"),
    status: str = typer.Option(None, help="FINISHED, SCHEDULED"),
    date_from: str = typer.Option(None, help="yyyy-MM-dd"),
    date_to: str = typer.Option(None, help="yyyy-MM-dd"),
    mode: str = typer.Option("sequential", help="sequential, threaded, async"),
    fmt: str = typer.Option("parquet", help="Output format: parquet, csv"),
    output: str = typer.Option(None, help="Output directory"),
):
    out = output or settings.output_dir
    client = _make_client()
    tasks = [("get_team_matches", {"team_id": team_id, "season": season, "status": status, "date_from": date_from, "date_to": date_to})]
    matches = _fetch(client, mode, tasks)[0]
    records = [FlatMatch.from_api(m).model_dump() for m in matches]
    write_records(records, out, fmt=fmt, partition_cols=["match_date"], batch_size=settings.batch_size)
    typer.echo(f"Wrote {len(records)} matches for team {team_id} → {out}/")
