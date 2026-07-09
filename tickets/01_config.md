# Ticket 1 — config.py

## What
`src/pingest/config.py` — single source of truth for runtime config using pydantic-settings.

## Fields
| Field | Env var | Default |
|---|---|---|
| `football_api_key` | `FOOTBALL_API_KEY` | required |
| `output_dir` | `PINGEST_OUTPUT_DIR` | `"data/out"` |
| `batch_size` | `PINGEST_BATCH_SIZE` | `10_000` |
| `api_rate_limit` | `PINGEST_API_RATE_LIMIT` | `10` |

## How
- Extend `BaseSettings` from `pydantic_settings`
- `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`
- Use `Field(validation_alias="FOOTBALL_API_KEY")` for the api key — the env var name doesn't match the field name
- Export `settings = Settings()` at module level

## Done when
```bash
uv run python -c "from pingest.config import settings; print(settings.football_api_key[:8])"
# 8874f65f
```
