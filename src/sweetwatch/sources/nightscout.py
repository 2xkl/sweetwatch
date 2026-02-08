"""Nightscout API client."""

import hashlib
from datetime import datetime, timezone

import httpx

from .base import CGMSource, GlucoseEntry, Trend

# Mapping Nightscout direction strings to unified Trend enum
DIRECTION_MAP: dict[str, Trend] = {
    "DoubleUp": Trend.RISING_FAST,
    "SingleUp": Trend.RISING,
    "FortyFiveUp": Trend.RISING_SLOW,
    "Flat": Trend.STABLE,
    "FortyFiveDown": Trend.FALLING_SLOW,
    "SingleDown": Trend.FALLING,
    "DoubleDown": Trend.FALLING_FAST,
    "NOT COMPUTABLE": Trend.UNKNOWN,
    "RATE OUT OF RANGE": Trend.UNKNOWN,
    "None": Trend.UNKNOWN,
}


class NightscoutSource(CGMSource):
    """CGM data source using Nightscout API."""

    def __init__(self, url: str, api_secret: str) -> None:
        self.url = url.rstrip("/")
        # Nightscout requires SHA1 hash of API_SECRET in the header
        self.api_secret_hash = hashlib.sha1(api_secret.encode()).hexdigest()
        self._http = httpx.AsyncClient(
            base_url=self.url,
            headers={"api-secret": self.api_secret_hash},
        )

    async def get_current(self) -> GlucoseEntry | None:
        """Get the most recent glucose reading."""
        entries = await self.get_entries(count=1)
        return entries[0] if entries else None

    async def get_entries(self, count: int = 10) -> list[GlucoseEntry]:
        """Get recent glucose readings from Nightscout."""
        resp = await self._http.get(
            "/api/v1/entries.json",
            params={"count": count},
        )
        resp.raise_for_status()
        data = resp.json()

        entries = []
        for item in data:
            if "sgv" not in item:
                continue

            direction = item.get("direction", "None")
            trend = DIRECTION_MAP.get(direction, Trend.UNKNOWN)

            # Nightscout returns timestamp in milliseconds
            ts_ms = item.get("date", 0)
            timestamp = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)

            entries.append(
                GlucoseEntry(
                    value=item["sgv"],
                    trend=trend,
                    timestamp=timestamp,
                )
            )

        return entries

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()
