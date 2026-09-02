import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./agent_economy.db"
    NEON: str = ""
    PLATFORM_FEE_RATE: float = 0.05
    MINIMUM_PLATFORM_FEE: float = 1.0  # 最低手数料 $1
    SUPERVISOR_APPROVAL_THRESHOLD_USD: float = 10.0
    LOG_LEVEL: str = "INFO"
    BASE_URL: str = "https://ai-qmtw.onrender.com"

    # Stripe configuration
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    class Config:
        env_file = ".env"

    @property
    def database_url(self) -> str:
        url = self.NEON.strip() or self.DATABASE_URL
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql+asyncpg://"):
            parts = urlsplit(url)
            query = parse_qsl(parts.query, keep_blank_values=True)
            query = [
                (key, value)
                for key, value in query
                if key not in {"sslmode", "channel_binding"}
            ]
            if not any(key == "ssl" for key, _ in query):
                query.append(("ssl", "require"))
            return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
        return url

settings = Settings()
