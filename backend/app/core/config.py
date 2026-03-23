"""
Environment-driven settings.

Loads from `.env` (local) and real environment variables (containers / K8s).
See `.env.example` at the repo root for variable names.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote_plus

from pydantic import AliasChoices, Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load env from repo root and/or `backend/` regardless of process cwd (uvicorn, pytest, alembic).
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_REPO_ROOT = _BACKEND_ROOT.parent
_ENV_FILES = tuple(
    str(p)
    for p in (_REPO_ROOT / ".env", _BACKEND_ROOT / ".env")
    if p.is_file()
)


class Settings(BaseSettings):
    """Application configuration; validated at startup."""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
        **({"env_file": _ENV_FILES} if _ENV_FILES else {}),
    )

    # --- Environment ---
    ENVIRONMENT: Literal["local", "dev", "staging", "production"] = Field(
        default="local",
        validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV"),
    )
    DEBUG: bool = False

    # Used by JWT/sessions later; set for parity with common starter templates.
    SECRET_KEY: str = Field(
        default="change-me-in-production-use-long-random-string",
        min_length=8,
        description="Signing secret for future auth; change in production.",
    )

    # --- API ---
    PROJECT_NAME: str = "Orion Paper Trading Copilot API"
    API_V1_PREFIX: str = "/api/v1"

    # --- MVP safety (kill switch) ---
    TRADING_ENABLED: bool = Field(
        default=True,
        description="When false, persist/approve/submit/place/exit are rejected (read-only).",
    )
    MAX_OPEN_POSITIONS: int = Field(
        default=20,
        ge=1,
        le=500,
        description="Broker open position count limit before submit (paper).",
    )

    # --- Market data (pluggable adapters: `stub` | `yfinance`) ---
    MARKET_DATA_PROVIDER: Literal["stub", "yfinance"] = "stub"

    # --- News & sentiment (`rules` until an LLM engine is wired) ---
    NEWS_PROVIDER: Literal["stub", "yfinance"] = "stub"
    SENTIMENT_ENGINE: Literal["rules", "llm"] = "rules"

    # --- Alpaca paper trading (https://paper-api.alpaca.markets) ---
    # Alias env names match common docs: ALPACA_API_KEY / ALPACA_API_SECRET
    ALPACA_API_KEY_ID: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ALPACA_API_KEY_ID", "ALPACA_API_KEY"),
    )
    ALPACA_API_SECRET_KEY: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "ALPACA_API_SECRET_KEY",
            "ALPACA_API_SECRET",
            "ALPACA_SECRET_KEY",
        ),
    )
    ALPACA_PAPER_BASE_URL: str = Field(
        default="https://paper-api.alpaca.markets",
        validation_alias=AliasChoices("ALPACA_PAPER_BASE_URL", "ALPACA_BASE_URL"),
    )

    # Optional: wire when adding NewsAPI / Finnhub adapters
    NEWS_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def _normalize_app_env(cls, v: Any) -> Any:
        if isinstance(v, str) and v.strip().lower() == "development":
            return "dev"
        return v

    # --- Database ---
    # Prefer a single URL; alternatively compose from parts below.
    DATABASE_URL: str | None = None
    POSTGRES_USER: str = "orion"
    POSTGRES_PASSWORD: str = "orion"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "orion"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_database_uri(self) -> str:
        """SQLAlchemy connection string (sync driver)."""
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2", 1)
        user = quote_plus(self.POSTGRES_USER)
        pwd = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql+psycopg2://{user}:{pwd}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # --- Pool (tune per deployment) ---
    DB_POOL_SIZE: int = Field(default=5, ge=1, le=50)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, le=100)

    # --- Background jobs (RQ + Redis) ---
    REDIS_URL: str = "redis://localhost:6379/0"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — use in FastAPI deps via `Depends`."""
    return Settings()


settings = get_settings()
