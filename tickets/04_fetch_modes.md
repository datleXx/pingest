# Ticket 4 — Fetch modes (sequential, threaded, async)

## What
Add `--mode` support to `FootballApiClient` — same pattern as `fetch_pages_sequential`, `fetch_pages_threaded`, `_run_async` you already built in `sources/api.py`.

## Important: why modes matter here
With 10 req/min rate limit, threaded/async don't speed up a single list of calls. The value is fetching **multiple independent endpoints at once** — e.g. standings + matches + scorers all start at t=0 and queue into the rate limiter together.

## What to build in `sources/football_api.py`

A task is just: `(method_name: str, kwargs: dict)`

```python
tasks = [
    ("get_competition_matches", {"competition": "PL", "season": 2024}),
    ("get_standings", {"competition": "PL", "season": 2024}),
]
```

### `fetch_sequential(client, tasks) -> list`
Call each task in order, return list of results. Trivial — just a loop.

### `fetch_threaded(client, tasks, max_workers=3) -> list`
Same as `fetch_pages_threaded` in sources/api.py:
- `ThreadPoolExecutor` with `as_completed`
- The `RateLimiter` lock on the client serializes HTTP calls automatically — no extra work needed
- Don't let one task failure kill the rest — catch `SourceError`, log it, continue
- Return results in task order

### `fetch_async(client, tasks) -> list`
Same as `_run_async` in sources/api.py:
- `asyncio.gather` to fire all tasks concurrently
- But `FootballApiClient._get` is sync — wrap each task call in `asyncio.to_thread(getattr(client, method), **kwargs)`
- `asyncio.to_thread` runs a sync function in a thread pool without blocking the event loop — no need to rewrite the client in async

## Done when
```bash
uv run python -c "
from pingest.config import settings
from pingest.sources.football_api import FootballApiClient, fetch_threaded
client = FootballApiClient(settings.football_api_key, settings.api_rate_limit)
tasks = [
    ('get_standings', {'competition': 'PL', 'season': 2024}),
    ('get_scorers', {'competition': 'PL', 'season': 2024}),
]
results = fetch_threaded(client, tasks)
print(len(results), 'results')
"
```
