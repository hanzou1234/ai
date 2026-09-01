from app.config import DEFAULT_SQLITE_DATABASE_URL, normalize_database_url
from app.config import Settings
from app.database import build_engine_kwargs


def test_normalize_database_url_keeps_sqlite_fallback():
    assert normalize_database_url(DEFAULT_SQLITE_DATABASE_URL) == DEFAULT_SQLITE_DATABASE_URL


def test_normalize_database_url_converts_postgres_scheme():
    assert normalize_database_url("postgres://db.example.com:5432/appdb") == (
        "postgresql+asyncpg://db.example.com:5432/appdb"
    )


def test_build_engine_kwargs_uses_sqlite_connect_args_only_for_sqlite():
    assert build_engine_kwargs("sqlite+aiosqlite:///./local.db") == {
        "echo": True,
        "connect_args": {"check_same_thread": False},
    }
    assert build_engine_kwargs("postgresql+asyncpg://db.example.com:5432/appdb") == {"echo": True}


def test_settings_normalizes_database_url_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://db.example.com:5432/appdb")
    assert Settings().DATABASE_URL == "postgresql+asyncpg://db.example.com:5432/appdb"
