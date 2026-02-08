"""Base classes for CGM data sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Trend(str, Enum):
    """Unified trend direction."""

    RISING_FAST = "RISING_FAST"
    RISING = "RISING"
    RISING_SLOW = "RISING_SLOW"
    STABLE = "STABLE"
    FALLING_SLOW = "FALLING_SLOW"
    FALLING = "FALLING"
    FALLING_FAST = "FALLING_FAST"
    UNKNOWN = "UNKNOWN"


@dataclass
class GlucoseEntry:
    """A single glucose reading."""

    value: int  # mg/dL
    trend: Trend
    timestamp: datetime


class CGMSource(ABC):
    """Abstract base class for CGM data sources."""

    @abstractmethod
    async def get_current(self) -> GlucoseEntry | None:
        """Get the most recent glucose reading."""
        ...

    @abstractmethod
    async def get_entries(self, count: int = 10) -> list[GlucoseEntry]:
        """Get recent glucose readings."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources."""
        ...
