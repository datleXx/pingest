# Ticket 5 — CLI subcommands

## What
Add football subcommands to `src/pingest/cli.py` — same pattern as `ingest-file` you already built.

## Pattern (same as ingest-file)
```
fetch → flatten with from_api() → write_parquet_partitioned
```

## Commands

### `pingest ingest-matches`
```
--competition   TEXT   e.g. PL, CL       [required]
--season        INT    e.g. 2024         [required]
--status        TEXT   FINISHED/SCHEDULED [default: None]
--mode          TEXT   sequential/threaded/async [default: sequential]
--output        TEXT   [default: settings.output_dir]
```
Flow:
```python
client = FootballApiClient(settings.football_api_key, settings.api_rate_limit)
matches = client.get_competition_matches(competition, season=season, status=status)
records = [FlatMatch.from_api(m).model_dump() for m in matches]
write_parquet_partitioned(records, output, partition_cols=["match_date"], batch_size=settings.batch_size)
```
Partition by: `match_date`

---

### `pingest ingest-standings`
```
--competition   TEXT   [required]
--season        INT    [required]
--output        TEXT   [default: settings.output_dir]
```
Note: standings response is a list of groups (e.g. TOTAL, HOME, AWAY). Each group has a `table` list. You need to flatten both levels — one row per team per group.

Partition by: `competition_code`

---

### `pingest ingest-scorers`
```
--competition   TEXT   [required]
--season        INT    [required]
--limit         INT    [default: 50]
--output        TEXT   [default: settings.output_dir]
```
Partition by: `competition_code`

---

### `pingest ingest-team`
```
--team-id       INT    [required]
--date-from     TEXT   yyyy-MM-dd
--date-to       TEXT   yyyy-MM-dd
--status        TEXT   FINISHED/SCHEDULED
--output        TEXT   [default: settings.output_dir]
```
Partition by: `match_date`

---

## Notes
- `settings` provides the API key and defaults — don't add `--api-key` as a CLI arg
- Print one line to stdout after each command: `"Wrote 380 records → data/out/"`
- Log start/end with record count using the existing `get_logger`

## Done when
```bash
uv run pingest ingest-matches --competition PL --season 2024 --status FINISHED
# Wrote 380 records → data/out/
```
