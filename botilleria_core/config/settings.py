from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ─────────────────────────────────────────────────
    database_url: str = "sqlite:///./botilleria.db"
    db_echo: bool = False

    # ── LLM (OpenRouter via LiteLlm, patrón wmill) ───────────────
    openrouter_api_key: str = ""
    model_name: str = "openrouter/nvidia/nemotron-3-super-120b-a12b:free"
    model_display: str = "nemotron-3-super-120b:free"

    # ── App ──────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
