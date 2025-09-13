from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List

from ..models.schemas import CapacityPoint, CapacityResponse
from ..repositories.capacity_repository import CapacityRepository
from ..config import get_alias_map


class ValidationError(ValueError):
    pass


@dataclass
class CapacityService:
    repo: CapacityRepository
    alias_map: dict = field(default_factory=lambda: get_alias_map())

    def get_capacity(self, corridor: str, date_from: date, date_to: date) -> CapacityResponse:
        self._validate_dates(date_from, date_to)
        corridor_norm = self.alias_map.get(corridor, corridor)
        rows = self.repo.get_capacity_with_rolling_avg(corridor_norm, date_from, date_to)
        points: List[CapacityPoint] = []
        for (_c, wk, teu, avg) in rows:
            if wk < date_from:
                continue
            iso = wk.isocalendar()  # ISO calendar: (year, week, weekday)
            points.append(
                CapacityPoint(
                    week_start_date=wk,
                    week_no=iso.week,
                    offered_capacity_teu=teu,
                )
            )
        return CapacityResponse(corridor=corridor, points=points)

    def _validate_dates(self, date_from: date, date_to: date) -> None:
        if date_from > date_to:
            raise ValidationError("date_from must be on or before date_to")
        # Avoid extremely large ranges
        if (date_to - date_from).days > 366 * 3:
            raise ValidationError("Range too large; please request <= 3 years")
