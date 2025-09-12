from __future__ import annotations

from app.config import ensure_schema, get_engine
from sqlalchemy import text


def main() -> None:
    ensure_schema()
    engine = get_engine()
    with engine.connect() as conn:
        tables = list(
            conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")).scalars()
        )
    print({"database": str(engine.url), "tables": tables})


if __name__ == "__main__":
    main()

