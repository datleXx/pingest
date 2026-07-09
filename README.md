# pingest

A CLI tool I built to pull soccer data from the [football-data.org](https://www.football-data.org) API and store it locally as partitioned Parquet or CSV files.

Started as a way to learn advanced Python. Ended up being something I actually use (for fun apparently).

---

## What it does

- Fetches matches, standings, and top scorers for any competition
- Pulls historical match data for a specific team
- Writes to partitioned Parquet or flat CSV
- Handles rate limiting transparently (free tier: 10 req/min)
- Supports sequential, threaded, and async fetch modes

## Setup

```bash
# clone and install
git clone https://github.com/datleXx/pingest
cd pingest
uv sync

# add your API key (get one free at football-data.org)
echo "FOOTBALL_API_KEY=keykeykeyabc" > .env
```

## Usage

Run it interactively — it'll walk you through everything:

```bash
uv run pingest
```

Or use subcommands directly:

```bash
# Premier League 2024 results
uv run pingest ingest-matches --competition PL --season 2024 --status FINISHED

# League table
uv run pingest ingest-standings --competition PL --season 2024

# Top scorers
uv run pingest ingest-scorers --competition PL --season 2024

# All matches for a team (Real Madrid = 86)
uv run pingest ingest-team --team-id 86 --season 2024

# Output as CSV instead of Parquet
uv run pingest ingest-standings --competition PL --season 2024 --fmt csv
```

Output goes to `data/out/` by default, partitioned by date or competition code.

## Competitions available (free tier)

`PL` Premier League · `CL` Champions League · `BL1` Bundesliga · `SA` Serie A · `PD` La Liga · `FL1` Ligue 1 · and 7 more.

## Stack

Python 3.13 · PyArrow · Pydantic · Typer · Questionary
