import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./agent_economy.db"
    PLATFORM_FEE_RATE: float = 0.05
    MINIMUM_PLATFORM_FEE: float = 1.0  # 最低手数料 $1
    LOG_LEVEL: str = "INFO"
    BASE_URL: str = "https://ai-qmtw.onrender.com"

    # Stripe configuration
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    class Config:
        env_file = ".env"

settings = Settings()
