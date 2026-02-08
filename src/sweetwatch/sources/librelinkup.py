"""LibreLinkUp API client."""

from datetime import datetime, timezone

import httpx

from .base import CGMSource, GlucoseEntry, Trend

# Mapping LibreLinkUp trend values to unified Trend enum
# LibreLinkUp uses numeric trend values (1-5) or text
TREND_MAP: dict[str | int, Trend] = {
    1: Trend.FALLING_FAST,
    2: Trend.FALLING,
    3: Trend.STABLE,
    4: Trend.RISING,
    5: Trend.RISING_FAST,
    "falling": Trend.FALLING,
    "stable": Trend.STABLE,
    "rising": Trend.RISING,
}


class LibreLinkUpSource(CGMSource):
    """CGM data source using LibreLinkUp API."""

    BASE_URLS: dict[str, str] = {
        "EU": "https://api-eu.libreview.io",
        "US": "https://api-us.libreview.io",
    }

    def __init__(self, username: str, password: str, region: str = "EU") -> None:
        self.username = username
        self.password = password
        self.base_url = self.BASE_URLS.get(region.upper(), self.BASE_URLS["EU"])
        self._token: str | None = None
        self._patient_id: str | None = None
        self._http = httpx.AsyncClient(base_url=self.base_url)

    async def _ensure_authenticated(self) -> None:
        """Authenticate if not already authenticated."""
        if self._token is None:
            await self._login()
        if self._patient_id is None:
            await self._get_patient_id()

    async def _login(self) -> None:
        """Authenticate with LibreLinkUp and store the auth token."""
        resp = await self._http.post(
            "/llu/auth/login",
            json={"email": self.username, "password": self.password},
            headers={
                "Content-Type": "application/json",
                "product": "llu.android",
                "version": "4.7.0",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["data"]["authTicket"]["token"]

    async def _get_patient_id(self) -> None:
        """Get the first patient connection ID."""
        resp = await self._http.get(
            "/llu/connections",
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        connections = resp.json()["data"]
        if connections:
            self._patient_id = connections[0]["patientId"]

    def _auth_headers(self) -> dict[str, str]:
        if not self._token:
            raise RuntimeError("Not authenticated. Call _login() first.")
        return {
            "Authorization": f"Bearer {self._token}",
            "product": "llu.android",
            "version": "4.7.0",
        }

    async def get_current(self) -> GlucoseEntry | None:
        """Get the most recent glucose reading."""
        entries = await self.get_entries(count=1)
        return entries[0] if entries else None

    async def get_entries(self, count: int = 10) -> list[GlucoseEntry]:
        """Get recent glucose readings from LibreLinkUp."""
        await self._ensure_authenticated()

        if not self._patient_id:
            return []

        resp = await self._http.get(
            f"/llu/connections/{self._patient_id}/graph",
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        data = resp.json()["data"]

        entries = []
        graph_data = data.get("graphData", [])

        for item in graph_data[-count:]:
            trend_value = item.get("TrendArrow", item.get("trend", 3))
            trend = TREND_MAP.get(trend_value, Trend.UNKNOWN)

            # Parse timestamp - LibreLinkUp uses various formats
            ts_str = item.get("Timestamp", item.get("timestamp", ""))
            try:
                timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                timestamp = datetime.now(timezone.utc)

            value = item.get("Value", item.get("value", 0))

            entries.append(
                GlucoseEntry(
                    value=int(value),
                    trend=trend,
                    timestamp=timestamp,
                )
            )

        return entries

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()
