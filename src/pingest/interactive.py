import time

import questionary
from pydantic import ValidationError as PydanticValidationError

from pingest.config import settings
from pingest.exception_helper.core import SinkError, SourceError
from pingest.logging_helper.core import get_logger
from pingest.models.soccer import FlatMatch, FlatScorer, FlatStanding
from pingest.sink import write_records
from pingest.sources.fetch import fetch_async, fetch_sequential, fetch_threaded
from pingest.sources.soccer_api import SoccerApiClient

logger = get_logger(__name__)

CURRENT_SEASON = 2026


def _make_client() -> SoccerApiClient:
    return SoccerApiClient(settings.football_api_key, settings.api_rate_limit)


def _pick_competition(client: SoccerApiClient) -> tuple[str, str]:
    competitions = client.get_competitions()
    choices = [f"{c['code']} — {c['name']}" for c in competitions]
    answer = questionary.select("Which competition?", choices=choices).ask()
    code = answer.split(" — ")[0]
    name = answer.split(" — ")[1]
    return code, name


def _pick_format() -> str:
    return questionary.select("Output format?", choices=["parquet", "csv"]).ask()


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
    fmt = _pick_format()
    output = settings.output_dir

    matches = client.get_competition_matches(
        code,
        season=season,
        status=None if status == "All" else status,
    )
    records = [FlatMatch.from_api(m).model_dump() for m in matches]
    write_records(
        records,
        output,
        fmt=fmt,
        partition_cols=["match_date"],
        batch_size=settings.batch_size,
    )
    print(f"\nWrote {len(records)} matches for {name} {season}/{output}/")


def _run_standings(client: SoccerApiClient) -> None:
    code, name = _pick_competition(client)
    season = _pick_season()
    fmt = _pick_format()
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
    write_records(
        records,
        output,
        fmt=fmt,
        partition_cols=["competition_code"],
        batch_size=settings.batch_size,
    )
    print(f"\nWrote {len(records)} standing rows for {name} {season}/{output}/")


def _run_scorers(client: SoccerApiClient) -> None:
    code, name = _pick_competition(client)
    season = _pick_season()
    fmt = _pick_format()
    output = settings.output_dir

    scorers = client.get_scorers(code, season=season)
    records = [
        FlatScorer.from_api(
            s, competition_code=code, season_start_year=season
        ).model_dump()
        for s in scorers
    ]
    write_records(
        records,
        output,
        fmt=fmt,
        partition_cols=["competition_code"],
        batch_size=settings.batch_size,
    )
    print(f"\nWrote {len(records)} scorers for {name} {season}/{output}/")


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
    fmt = _pick_format()
    output = settings.output_dir

    matches = client.get_team_matches(
        int(team_id_str),
        season=season,
        status=None if status == "All" else status,
    )
    records = [FlatMatch.from_api(m).model_dump() for m in matches]
    write_records(
        records,
        output,
        fmt=fmt,
        partition_cols=["match_date"],
        batch_size=settings.batch_size,
    )
    print(f"\nWrote {len(records)} matches for team {team_id_str}/{output}/")


def _flatten_standings(raw_standings: list[dict], code: str, season: int) -> list[dict]:
    records = []
    for group in raw_standings:
        for row in group["table"]:
            records.append(
                FlatStanding.from_api(
                    row,
                    competition_code=code,
                    season_start_year=season,
                    stage=group["stage"],
                    type=group["type"],
                ).model_dump()
            )
    return records


def _run_season_dump(client: SoccerApiClient) -> None:
    """Fetch matches + standings + scorers for one competition in parallel.
    Runs all three modes and prints timing so you can see the difference."""
    code, name = _pick_competition(client)
    season = _pick_season()
    output = settings.output_dir

    tasks = [
        ("get_competition_matches", {"competition": code, "season": season}),
        ("get_standings", {"competition": code, "season": season}),
        ("get_scorers", {"competition": code, "season": season}),
    ]

    mode = questionary.select(
        "Fetch mode?",
        choices=["sequential", "threaded", "async"],
    ).ask()

    print(f"\nFetching matches + standings + scorers for {name} {season} [{mode}]...")
    t0 = time.perf_counter()

    if mode == "threaded":
        results = fetch_threaded(client, tasks, max_workers=3)
    elif mode == "async":
        results = fetch_async(client, tasks)
    else:
        results = fetch_sequential(client, tasks)

    elapsed = time.perf_counter() - t0
    matches_raw, standings_raw, scorers_raw = results

    match_records = [FlatMatch.from_api(m).model_dump() for m in matches_raw]
    standing_records = _flatten_standings(standings_raw, code, season)
    scorer_records = [
        FlatScorer.from_api(
            s, competition_code=code, season_start_year=season
        ).model_dump()
        for s in scorers_raw
    ]

    fmt = _pick_format()
    write_records(
        match_records,
        output,
        fmt=fmt,
        partition_cols=["match_date"],
        batch_size=settings.batch_size,
    )
    write_records(
        standing_records,
        output,
        fmt=fmt,
        partition_cols=["competition_code"],
        batch_size=settings.batch_size,
    )
    write_records(
        scorer_records,
        output,
        fmt=fmt,
        partition_cols=["competition_code"],
        batch_size=settings.batch_size,
    )

    print(f"\n Season dump complete in {elapsed:.2f}s [{mode}]")
    print(
        f"  {len(match_records)} matches  |  {len(standing_records)} standing rows  |  {len(scorer_records)} scorers"
    )
    print(f" /{output}/")


def _run_bulk_standings(client: SoccerApiClient) -> None:
    """Fetch standings for ALL available competitions at once."""
    season = _pick_season()
    output = settings.output_dir

    print("\nFetching all available competitions...")
    competitions = client.get_competitions()
    tasks = [
        ("get_standings", {"competition": c["code"], "season": season})
        for c in competitions
    ]

    mode = questionary.select(
        "Fetch mode?",
        choices=["sequential", "threaded", "async"],
    ).ask()
    fmt = _pick_format()

    print(f"\nFetching standings for {len(tasks)} competitions [{mode}]...")

    t0 = time.perf_counter()

    if mode == "threaded":
        results = fetch_threaded(client, tasks, max_workers=len(tasks))
    elif mode == "async":
        results = fetch_async(client, tasks)
    else:
        results = fetch_sequential(client, tasks)

    elapsed = time.perf_counter() - t0

    all_records = []
    for standings_raw, comp in zip(results, competitions):
        if standings_raw:
            all_records.extend(_flatten_standings(standings_raw, comp["code"], season))
    write_records(
        all_records,
        output,
        fmt=fmt,
        partition_cols=["competition_code"],
        batch_size=settings.batch_size,
    )

    print(f"Bulk standings complete in {elapsed:.2f}s [{mode}]")
    print(
        f"  {len(all_records)} total rows across {len(competitions)} competitions/{output}/"
    )


ACTIONS = {
    "Matches — fetch match results for a competition": _run_matches,
    "Standings — fetch the league table": _run_standings,
    "Scorers — fetch top goalscorers": _run_scorers,
    "Team — fetch matches for a specific team": _run_team,
    "Season dump — matches + standings + scorers": _run_season_dump,
    "Bulk standings — all competitions at once": _run_bulk_standings,
}


def _run_action(action_fn, client: SoccerApiClient) -> None:
    try:
        action_fn(client)
    except SourceError as e:
        print(f"\nAPI error: {e}")
        print("  Check your internet connection or API key.")
    except SinkError as e:
        print(f"\nFailed to write data: {e}")
        print(f"  Make sure the output directory '{settings.output_dir}' is writable.")
    except PydanticValidationError as e:
        print(f"\nUnexpected data format from API: {e}")
        print("  The API may have changed its response shape.")
    except KeyboardInterrupt:
        print("\n  Cancelled.")


def start() -> None:
    print("\nWelcome to Pingest — soccer data ingestion tool.")
    print("Fetching available competitions...\n")

    try:
        client = _make_client()
    except SourceError as e:
        print(f"Could not connect to the API: {e}")
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
