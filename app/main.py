from __future__ import annotations

from fastapi import FastAPI

from .routes.health import router as health_router
from .routes.capacity import router as capacity_router
from .config import ensure_schema


def create_app() -> FastAPI:
    app = FastAPI(title="Capacity Service", version="0.1.0")
    app.include_router(health_router)
    app.include_router(capacity_router)
    # Dev convenience: ensure schema for local SQLite
    try:
        ensure_schema()
    except Exception:
        # In production, migrations should manage schema. Silently ignore here.
        pass
    return app


app = create_app()
