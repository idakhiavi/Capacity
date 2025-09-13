from fastapi.testclient import TestClient

from app.main import create_app


def test_capacity_bad_date_range_returns_400():
    app = create_app()
    client = TestClient(app)
    r = client.get(
        "/capacity",
        params={
            "date_from": "2024-02-12",
            "date_to": "2024-01-15",
        },
    )
    assert r.status_code == 400
    assert "date_from" in r.json().get("detail", "")

