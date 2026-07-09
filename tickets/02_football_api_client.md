# Ticket 2 — FootballApiClient

## What
`src/pingest/sources/football_api.py` — rate-limited HTTP client for api.football-data.org v4.

## RateLimiter class
Same idea as the `asyncio.Semaphore` you used in sources/api.py, but for sync code.

```python
class RateLimiter:
    def __init__(self, calls_per_minute: int): ...
    def acquire(self) -> None: ...
```

- Track call timestamps in a `collections.deque`
- On `acquire()`: drop timestamps older than 60s, if `len >= limit` sleep until the oldest falls outside the window
- Use a `threading.Lock` to make it thread-safe (same reason you used a semaphore in async)

## FootballApiClient class
Same pattern as `get_page` in `sources/api.py` — a `requests.Session` with auth pre-set.

```python
class FootballApiClient:
    def __init__(self, api_key: str, calls_per_minute: int = 10):
        # session with X-Auth-Token header pre-set
        # instantiate RateLimiter

    def _get(self, path: str, params: dict | None = None) -> Any:
        # 1. self._limiter.acquire()
        # 2. self._session.get(BASE_URL + path, params=params)
        # 3. if 429: read Retry-After header, sleep, retry once
        # 4. tenacity retry on 5xx/ConnectionError (same should_retry pattern from sources/api.py, but guard response is None)
        # 5. on error: raise SourceError with the message from JSON body
        # 6. log every request: url, params, status
```

## Endpoint methods
All optional params default to `None` and only added to params dict when not None — same pattern as `fetch_pages_sequential`.

| Method | Path | Returns |
|---|---|---|
| `get_competitions(areas=None)` | `/competitions` | `data["competitions"]` |
| `get_standings(competition, season=None)` | `/competitions/{id}/standings` | `data["standings"]` |
| `get_scorers(competition, season=None, limit=50)` | `/competitions/{id}/scorers` | `data["scorers"]` |
| `get_competition_matches(competition, season, status, date_from, date_to)` | `/competitions/{id}/matches` | `data["matches"]` |
| `get_competition_teams(competition, season=None)` | `/competitions/{id}/teams` | `data["teams"]` |
| `get_team_matches(team_id, season, status, date_from, date_to, limit=100)` | `/teams/{id}/matches` | `data["matches"]` |

## Done when
```bash
uv run python -c "
from pingest.config import settings
from pingest.sources.football_api import FootballApiClient
client = FootballApiClient(settings.football_api_key, settings.api_rate_limit)
matches = client.get_competition_matches('PL', season=2024, status='FINISHED')
print(len(matches), matches[0]['homeTeam']['name'])
"
```
