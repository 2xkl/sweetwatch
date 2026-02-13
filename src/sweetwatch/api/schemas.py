"""API response schemas."""

from datetime import datetime

from pydantic import BaseModel, computed_field


class GlucoseResponse(BaseModel):
    """Single glucose reading response."""

    id: int
    value: float
    trend: int
    timestamp: datetime

    @computed_field
    @property
    def trend_arrow(self) -> str:
        """Convert trend integer to arrow symbol."""
        arrows = {
            1: "↓↓",  # FALLING_FAST
            2: "↓",   # FALLING
            3: "→",   # STABLE
            4: "↑",   # RISING
            5: "↑↑",  # RISING_FAST
        }
        return arrows.get(self.trend, "?")

    model_config = {"from_attributes": True}


class GlucoseHistoryResponse(BaseModel):
    """Historical glucose readings response."""

    readings: list[GlucoseResponse]
    count: int


class SyncResponse(BaseModel):
    """Sync operation response."""

    synced: int
    status: str
