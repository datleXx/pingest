import questionary
from pydantic import ValidationError as PydanticValidationError

from pingest.config import settings
from pingest.exception_helper.core import SinkError, SourceError
from pingest.logging_helper.core import get_logger
from pingest.models.soccer import FlatMatch, FlatScorer, FlatStanding
from pingest.sink import write_parquet_partitioned
from pingest.sources.soccer_api import SoccerApiClient

logger = get_logger(__name__)

CURRENT_SEASON = 2024


def _make_client() -> SoccerApiClient:
    return SoccerApiClient(settings.football_api_key, settings.api_rate_limit)


def _pick_competition(client: SoccerApiClient) -> tuple[str, str]:
    competitions = client.get_competitions()
    choices = [f"{c['code']} — {c['name']}" for c in competitions]
    answer = questionary.select("Which competition?", choices=choices).ask()
    code = answer.split(" — ")[0]
    name = answer.split(" — ")[1]
    return code, name


def _pick_season() -> int:
    answer = questionary.text(
        "Which season? (enter start year)",
        default=str(CURRENT_SEASON),
        validate=lambda v: v.isdigit() or "Enter a valid year e.g. 2024",
    ).ask()
    return int(answer)


def _run_matches(client: SoccerApiClient) -> None:
    code, name = _pick_competition(client)
    season = _pick_season()
    status = questionary.select(
        "Match status?",
        choices=["All", "FINISHED", "SCHEDULED", "LIVE"],
    ).ask()
    output = settings.output_dir

    matches = client.get_competition_matches(
        code,
        season=season,
        status=None if status == "All" else status,
    )
    records = [FlatMatch.from_api(m).model_dump() for m in matches]
    write_parquet_partitioned(
        records, output, partition_cols=["match_date"], batch_size=settings.batch_size
    )
    print(f"\n✓ Wrote {len(records)} matches for {name} {season} → {output}/")


def _run_standings(client: SoccerApiClient) -> None:
    code, name = _pick_competition(client)
    season = _pick_season()
    output = settings.output_dir

    standings = client.get_standings(code, season=season)
    records = []
    for group in standings:
        for row in group["table"]:
            flat = FlatStanding.from_api(
                row,
                competition_code=code,
                season_start_year=season,
                stage=group["stage"],
                type=group["type"],
            )
            records.append(flat.model_dump())
    write_parquet_partitioned(
        records,
        output,
        partition_cols=["competition_code"],
        batch_size=settings.batch_size,
    )
    print(f"\n✓ Wrote {len(records)} standing rows for {name} {season} → {output}/")


def _run_scorers(client: SoccerApiClient) -> None:
    code, name = _pick_competition(client)
    season = _pick_season()
    output = settings.output_dir

    scorers = client.get_scorers(code, season=season)
    records = [
        FlatScorer.from_api(
            s, competition_code=code, season_start_year=season
        ).model_dump()
        for s in scorers
    ]
    write_parquet_partitioned(
        records,
        output,
        partition_cols=["competition_code"],
        batch_size=settings.batch_size,
    )
    print(f"\n✓ Wrote {len(records)} scorers for {name} {season} → {output}/")


def _run_team(client: SoccerApiClient) -> None:
    team_id_str = questionary.text(
        "Enter team ID (e.g. 86 for Real Madrid):",
        validate=lambda v: v.isdigit() or "Enter a numeric team ID",
    ).ask()
    season = _pick_season()
    status = questionary.select(
        "Match status?",
        choices=["All", "FINISHED", "SCHEDULED"],
    ).ask()
    output = settings.output_dir

    matches = client.get_team_matches(
        int(team_id_str),
        season=season,
        status=None if status == "All" else status,
    )
    records = [FlatMatch.from_api(m).model_dump() for m in matches]
    write_parquet_partitioned(
        records, output, partition_cols=["match_date"], batch_size=settings.batch_size
    )
    print(f"\n✓ Wrote {len(records)} matches for team {team_id_str} → {output}/")


ACTIONS = {
    "Matches — fetch match results for a competition": _run_matches,
    "Standings — fetch the league table": _run_standings,
    "Scorers — fetch top goalscorers": _run_scorers,
    "Team — fetch matches for a specific team": _run_team,
}


def _run_action(action_fn, client: SoccerApiClient) -> None:
    try:
        action_fn(client)
    except SourceError as e:
        print(f"\n✗ API error: {e}")
        print("  Check your internet connection or API key.")
    except SinkError as e:
        print(f"\n✗ Failed to write data: {e}")
        print(f"  Make sure the output directory '{settings.output_dir}' is writable.")
    except PydanticValidationError as e:
        print(f"\n✗ Unexpected data format from API: {e}")
        print("  The API may have changed its response shape.")
    except KeyboardInterrupt:
        print("\n  Cancelled.")


def start() -> None:
    print("\nWelcome to Pingest — soccer data ingestion tool.")
    print("Fetching available competitions...\n")

    try:
        client = _make_client()
    except SourceError as e:
        print(f"✗ Could not connect to the API: {e}")
        print("  Check your FOOTBALL_API_KEY in .env")
        return

    while True:
        action = questionary.select(
            "What are you interested in?",
            choices=list(ACTIONS.keys()) + ["Exit"],
        ).ask()

        if action == "Exit" or action is None:
            print("Bye!")
            break

        _run_action(ACTIONS[action], client)

        again = questionary.confirm("\nIngest something else?", default=True).ask()
        if not again:
            print("Bye!")
            break
