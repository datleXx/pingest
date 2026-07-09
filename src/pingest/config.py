from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    football_api_key: str = Field(validation_alias="FOOTBALL_API_KEY")
    output_dir: str = Field(default="data/out", validation_alias="PINGEST_OUTPUT_DIR")
    batch_size: int = Field(default=10_000, validation_alias="PINGEST_BATCH_SIZE")
    api_rate_limit: int = Field(default=10, validation_alias="PINGEST_API_RATE_LIMIT")


settings = Settings()
