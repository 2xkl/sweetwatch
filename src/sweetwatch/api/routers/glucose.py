"""Glucose API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from sweetwatch.api.schemas import GlucoseHistoryResponse, GlucoseResponse, SyncResponse
from sweetwatch.db.engine import get_db
from sweetwatch.services.glucose import glucose_service

router = APIRouter(prefix="/api/glucose", tags=["glucose"])


@router.get("/current", response_model=GlucoseResponse)
async def get_current_glucose(db: Session = Depends(get_db)) -> GlucoseResponse:
    """Get the most recent glucose reading."""
    reading = glucose_service.get_current(db)
    if not reading:
        raise HTTPException(status_code=404, detail="No glucose readings found")

    return GlucoseResponse(
        id=reading.id,
        value=reading.value,
        trend=reading.trend or 3,
        timestamp=reading.timestamp,
    )


@router.get("/history", response_model=GlucoseHistoryResponse)
async def get_glucose_history(
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=288, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> GlucoseHistoryResponse:
    """Get historical glucose readings."""
    readings = glucose_service.get_history(db, hours=hours, limit=limit)

    response_readings = [
        GlucoseResponse(
            id=r.id,
            value=r.value,
            trend=r.trend or 3,
            timestamp=r.timestamp,
        )
        for r in readings
    ]

    return GlucoseHistoryResponse(readings=response_readings, count=len(response_readings))


@router.post("/sync", response_model=SyncResponse)
async def sync_glucose(db: Session = Depends(get_db)) -> SyncResponse:
    """Manually trigger sync from LibreLinkUp."""
    try:
        stored = await glucose_service.fetch_and_store(db)
        return SyncResponse(synced=len(stored), status="ok")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
