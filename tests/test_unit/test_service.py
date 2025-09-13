from datetime import date, timedelta

import pytest

from app.services.capacity_service import CapacityService, ValidationError


class FakeRepo:
    def __init__(self, rows):
        self._rows = rows

    def get_capacity_with_rolling_avg(self, corridor, date_from, date_to):
        return self._rows


def test_service_filters_buffer_and_rounds():
    corridor = "ASIA-EUR"
    d0 = date(2024, 1, 1)
    rows = [
        (corridor, d0 - timedelta(days=21), 90, 90.0),
        (corridor, d0 - timedelta(days=14), 100, 95.0),
        (corridor, d0 - timedelta(days=7), 110, 100.0),
        (corridor, d0, 120, 105.0),
        (corridor, d0 + timedelta(days=7), 130, 115.0),
    ]
    svc = CapacityService(repo=FakeRepo(rows))
    resp = svc.get_capacity(corridor, d0, d0 + timedelta(days=7))
    assert resp.corridor == corridor
    assert [p.week_start_date for p in resp.points] == [d0, d0 + timedelta(days=7)]
    # ISO week numbers for 2024-01-01 is week 1
    assert resp.points[0].week_no >= 1
    assert resp.points[0].offered_capacity_teu == 120


def test_validation_rejects_bad_range():
    svc = CapacityService(repo=FakeRepo([]))
    with pytest.raises(ValidationError):
        svc.get_capacity("X", date(2024, 1, 10), date(2024, 1, 1))
