from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.routes.capacity import get_service
from app.repositories.capacity_repository import CapacityRepository
from app.services.capacity_service import CapacityService


def make_sqlite_engine():
    # Use StaticPool to ensure the same in-memory DB is reused across connections
    # so the seeded data remains visible to the app under test.
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def seed(conn):
    conn.execute(text(
        """
        CREATE TABLE weekly_capacity (
          corridor TEXT NOT NULL,
          week_start_date DATE NOT NULL,
          offered_teu INTEGER NOT NULL
        );
        """
    ))
    corridor = "china_main-north_europe_main"  # canonical stored value
    start = date(2024, 1, 1)
    data = [
        (corridor, start + timedelta(days=7 * i), 100 + 10 * i) for i in range(6)
    ]
    for c, d, teu in data:
        conn.execute(text("INSERT INTO weekly_capacity VALUES (:c, :d, :t)"), {"c": c, "d": d, "t": teu})


def override_service(engine):
    repo = CapacityRepository(engine)
    return CapacityService(repo)


def test_capacity_endpoint_sqlite():
    engine = make_sqlite_engine()
    with engine.begin() as conn:
        seed(conn)

    app = create_app()

    def _override():
        return override_service(engine)

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
    points = data["points"]
    # Expect 5 weekly points between 2024-01-15 and 2024-02-12 inclusive
    assert len(points) == 5
    # Validate schema keys present
    for p in points:
        assert set(["week_start_date", "week_no", "offered_capacity_teu", "rolling_avg_4w"]).issubset(p.keys())
