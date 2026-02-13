"""Glucose data service - coordinates CGM source and database storage."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from sweetwatch.config import settings
from sweetwatch.models.glucose import GlucoseReading
from sweetwatch.sources.base import Trend
from sweetwatch.sources.librelinkup import LibreLinkUpSource


class GlucoseService:
    """Service for fetching and storing glucose readings."""

    def __init__(self) -> None:
        self._source: LibreLinkUpSource | None = None

    async def _get_source(self) -> LibreLinkUpSource:
        """Get or create the LibreLinkUp source."""
        if self._source is None:
            self._source = LibreLinkUpSource(
                username=settings.libre_username,
                password=settings.libre_password,
                region=settings.libre_region,
            )
        return self._source

    async def fetch_and_store(self, db: Session, count: int = 50) -> list[GlucoseReading]:
        """Fetch readings from LibreLinkUp and store new ones in database."""
        source = await self._get_source()
        entries = await source.get_entries(count=count)

        stored = []
        for entry in entries:
            # Check if reading already exists (by timestamp)
            existing = (
                db.query(GlucoseReading)
                .filter(GlucoseReading.timestamp == entry.timestamp)
                .first()
            )

            if not existing:
                reading = GlucoseReading(
                    patient_id=source._patient_id or "default",
                    value=float(entry.value),
                    trend=self._trend_to_int(entry.trend),
                    timestamp=entry.timestamp,
                )
                db.add(reading)
                stored.append(reading)

        if stored:
            db.commit()
        return stored

    def get_current(self, db: Session) -> GlucoseReading | None:
        """Get the most recent reading from database."""
        return (
            db.query(GlucoseReading)
            .order_by(GlucoseReading.timestamp.desc())
            .first()
        )

    def get_history(
        self, db: Session, hours: int = 24, limit: int = 288
    ) -> list[GlucoseReading]:
        """Get historical readings from database."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return (
            db.query(GlucoseReading)
            .filter(GlucoseReading.timestamp >= cutoff)
            .order_by(GlucoseReading.timestamp.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def _trend_to_int(trend: Trend) -> int:
        """Convert Trend enum to integer for storage."""
        mapping = {
            Trend.FALLING_FAST: 1,
            Trend.FALLING: 2,
            Trend.FALLING_SLOW: 2,
            Trend.STABLE: 3,
            Trend.RISING_SLOW: 4,
            Trend.RISING: 4,
            Trend.RISING_FAST: 5,
            Trend.UNKNOWN: 3,
        }
        return mapping.get(trend, 3)

    async def close(self) -> None:
        """Close the source connection."""
        if self._source:
            await self._source.close()
            self._source = None


# Singleton instance
glucose_service = GlucoseService()
