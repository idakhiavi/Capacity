import os
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.main import create_app
from app.routes.capacity import get_service
from app.repositories.capacity_repository import CapacityRepository
from app.services.capacity_service import CapacityService


def _mysql_url():
    return os.getenv("DATABASE_URL")


@pytest.mark.skipif(not _mysql_url(), reason="DATABASE_URL not set for MySQL test")
def test_capacity_endpoint_mysql():
    engine = create_engine(_mysql_url(), future=True)
    corridor = "china_main-north_europe_main"  # canonical stored value
    start = date(2024, 1, 1)
    with engine.begin() as conn:
        try:
            conn.execute(text("DELETE FROM weekly_capacity"))
        except Exception:
            conn.execute(text(
                """
                CREATE TABLE weekly_capacity (
                  corridor TEXT NOT NULL,
                  week_start_date DATE NOT NULL,
                  offered_teu INTEGER NOT NULL
                );
                """
            ))
        data = [
            (corridor, start + timedelta(days=7 * i), 100 + 10 * i) for i in range(7)
        ]
        for c, d, teu in data:
            conn.execute(text("INSERT INTO weekly_capacity VALUES (:c, :d, :t)"), {"c": c, "d": d, "t": teu})

    app = create_app()

    def _override():
        return CapacityService(CapacityRepository(engine))

    app.dependency_overrides[get_service] = _override
    client = TestClient(app)

    r = client.get(
        "/capacity",
        params={
            "date_from": "2024-01-15",
            "date_to": "2024-02-12",
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["points"]) >= 4
