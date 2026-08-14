from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./agent_economy.db"
    PLATFORM_FEE_RATE: float = 0.05
    MINIMUM_PLATFORM_FEE: float = 1.0  # 最低手数料 $1
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
