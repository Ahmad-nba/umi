from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "feedback-watch-tower"
    app_env: str = "development"
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="openrouter/auto", alias="OPENROUTER_MODEL")
    database_url: str = "sqlite:///./data/feedback_watch_tower.db"
    sender_api_key: str | None = Field(default=None, alias="SENDER_API_KEY")
    sender_from_email: str | None = Field(default=None, alias="SENDER_FROM_EMAIL")
    sender_from_name: str = Field(
        default="UMI Feedback Watch Tower", alias="SENDER_FROM_NAME"
    )
    sender_enabled: bool = Field(default=False, alias="SENDER_ENABLED")
    sender_api_url: str = Field(
        default="https://api.sender.net/v1/email", alias="SENDER_API_URL"
    )
    frontend_base_url: str = Field(
        default="http://localhost:3000", alias="FRONTEND_BASE_URL"
    )
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ORIGINS",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [origin.strip().rstrip("/") for origin in self.cors_origins.split(",")]
        origins = [origin for origin in origins if origin]
        if "*" in origins and self.app_env.lower() == "production":
            raise ValueError("CORS_ORIGINS cannot contain '*' in production")
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
