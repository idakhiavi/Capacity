from __future__ import annotations

import logging
import os
from typing import Optional

from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class Settings(BaseSettings):
    app_name: str = "capacity-service"
    database_url: str = os.getenv("DATABASE_URL", "sqlite+pysqlite:///./.data.sqlite")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    corridor_alias_file: str = os.getenv("CORRIDOR_ALIAS_FILE", "config/corridor_aliases.json")

    class Config:
        env_prefix = ""
        case_sensitive = False


_engine: Optional[Engine] = None


def get_settings() -> Settings:
    return Settings()


def _configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s - %(message)s")


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.database_url, future=True)
        _configure_logging(settings.log_level)
    return _engine


def ensure_schema(engine: Optional[Engine] = None) -> None:
    """Create expected table if it doesn't exist (dev/test convenience)."""
    engine = engine or get_engine()
    ddl = """
    CREATE TABLE IF NOT EXISTS weekly_capacity (
        corridor TEXT NOT NULL,
        week_start_date DATE NOT NULL,
        offered_teu INTEGER NOT NULL
    );
    """
    idx1 = "CREATE INDEX IF NOT EXISTS idx_weekly_capacity_corridor ON weekly_capacity(corridor);"
    idx2 = "CREATE INDEX IF NOT EXISTS idx_weekly_capacity_week ON weekly_capacity(week_start_date);"
    with engine.begin() as conn:
        conn.execute(text(ddl))
        try:
            conn.execute(text(idx1))
        except Exception:
            pass
        try:
            conn.execute(text(idx2))
        except Exception:
            pass


def get_alias_map(settings: Optional[Settings] = None) -> dict:
    settings = settings or get_settings()
    path = settings.corridor_alias_file
    try:
        if os.path.isfile(path):
            import json
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    return {
        "ASIA-EUR": "china_main-north_europe_main",
    }

