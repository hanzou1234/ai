import os
from pydantic import field_validator
from pydantic_settings import BaseSettings

DEFAULT_SQLITE_DATABASE_URL = "sqlite+aiosqlite:///./agent_economy.db"


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url


class Settings(BaseSettings):
    DATABASE_URL: str = DEFAULT_SQLITE_DATABASE_URL
    PLATFORM_FEE_RATE: float = 0.05
    MINIMUM_PLATFORM_FEE: float = 1.0  # 最低手数料 $1
    SUPERVISOR_APPROVAL_THRESHOLD_USD: float = 10.0
    LOG_LEVEL: str = "INFO"
    BASE_URL: str = "https://ai-qmtw.onrender.com"

    # Stripe configuration
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        return normalize_database_url(value)

    class Config:
        env_file = ".env"

settings = Settings()
