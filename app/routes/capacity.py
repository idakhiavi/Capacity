from __future__ import annotations

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query

from ..config import get_engine
from ..models.schemas import CapacityResponse
from ..repositories.capacity_repository import CapacityRepository
from ..services.capacity_service import CapacityService, ValidationError


router = APIRouter(prefix="/capacity", tags=["capacity"])


def get_service() -> CapacityService:
    repo = CapacityRepository(get_engine())
    return CapacityService(repo=repo)


@router.get(
    "",
    response_model=CapacityResponse,
    summary="Weekly capacity with 4-week rolling average",
    tags=["capacity"],
)
def read_capacity(
    date_from: date = Query(..., description="Start date (YYYY-MM-DD) inclusive"),
    date_to: date = Query(..., description="End date (YYYY-MM-DD) inclusive"),
    service: CapacityService = Depends(get_service),
):
    # Corridor is fixed per task requirements; alias map normalizes internally
    corridor = "ASIA-EUR"
    try:
        return service.get_capacity(corridor=corridor, date_from=date_from, date_to=date_to)
    except ValidationError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
