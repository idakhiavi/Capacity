from __future__ import annotations

from datetime import date
from typing import List

from pydantic import BaseModel, Field


class CapacityPoint(BaseModel):
    week_start_date: date = Field(..., description="Start date of the ISO week")
    week_no: int = Field(..., ge=1, le=53)
    offered_capacity_teu: int = Field(..., ge=0)
    rolling_avg_4w: float = Field(..., ge=0)


class CapacityResponse(BaseModel):
    corridor: str
    points: List[CapacityPoint]
