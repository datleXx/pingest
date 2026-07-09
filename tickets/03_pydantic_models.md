# Ticket 3 — Pydantic models (flatten API responses)

## What
`src/pingest/models/football.py` — flatten nested API dicts into Parquet-ready rows.

Same idea as `TaxiRecord` in models.py, but the API returns nested dicts so you need to flatten manually.

## Why
`write_parquet_partitioned` calls `pa.Table.from_pylist(batch)`. PyArrow can't handle nested dicts — everything must be a flat key/value. A raw match looks like:
```json
{ "homeTeam": { "name": "Arsenal" }, "score": { "fullTime": { "home": 2 } } }
```
Must become:
```json
{ "home_team_name": "Arsenal", "home_score_ft": 2 }
```

## Models to build

### FlatMatch
Fields to extract from a raw match dict:
- `competition_code` — from `competition.code`
- `season_start_year` — from `season.startDate[:4]`
- `match_id` — from `id`
- `utc_date` — from `utcDate`
- `match_date` — from `utcDate[:10]` (partition key)
- `status` — from `status`
- `matchday` — from `matchday`
- `home_team_id`, `home_team_name` — from `homeTeam.id`, `homeTeam.name`
- `away_team_id`, `away_team_name` — from `awayTeam.id`, `awayTeam.name`
- `home_score_ft`, `away_score_ft` — from `score.fullTime.home/away`
- `winner` — from `score.winner`

### FlatStanding
Fields per row (one row per team per table):
- `competition_code`, `season_start_year`, `stage`, `type`
- `position`, `team_id`, `team_name`
- `played`, `won`, `drawn`, `lost`, `points`, `goals_for`, `goals_against`, `goal_difference`, `form`

### FlatScorer
- `competition_code`, `season_start_year`
- `player_id`, `player_name`, `nationality`
- `team_id`, `team_name`
- `goals`, `assists`, `penalties`

## Interface
Each model needs a classmethod that accepts the raw dict:
```python
@classmethod
def from_api(cls, raw: dict) -> "FlatMatch":
    return cls(
        competition_code=raw["competition"]["code"],
        home_team_name=raw["homeTeam"]["name"],
        home_score_ft=raw["score"]["fullTime"]["home"],
        ...
    )
```

Use `model_dump()` when passing to the sink — same as `TaxiRecord.model_dump()`.

## Done when
```bash
uv run python -c "
from pingest.config import settings
from pingest.sources.football_api import FootballApiClient
from pingest.models.football import FlatMatch
client = FootballApiClient(settings.football_api_key, settings.api_rate_limit)
matches = client.get_competition_matches('PL', season=2024, status='FINISHED')
flat = FlatMatch.from_api(matches[0])
print(flat.model_dump())
"
```
