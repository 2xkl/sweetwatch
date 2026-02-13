"""LibreLinkUp API client."""

import hashlib
import logging
from datetime import datetime, timezone

import httpx

from .base import CGMSource, GlucoseEntry, Trend

logger = logging.getLogger(__name__)

# Mapping LibreLinkUp trend values to unified Trend enum
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

# User agent mimicking iOS app
USER_AGENT = "Mozilla/5.0 (iPhone; CPU OS 17_4.1 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/17.4.1 Mobile/10A5355d Safari/8536.25"


class LibreLinkUpSource(CGMSource):
    """CGM data source using LibreLinkUp API."""

    BASE_URLS: dict[str, str] = {
        "EU": "https://api-eu.libreview.io",
        "US": "https://api-us.libreview.io",
        "EU2": "https://api-eu2.libreview.io",
        "AE": "https://api-ae.libreview.io",
        "AP": "https://api-ap.libreview.io",
        "AU": "https://api-au.libreview.io",
        "CA": "https://api-ca.libreview.io",
        "DE": "https://api-de.libreview.io",
        "FR": "https://api-fr.libreview.io",
        "JP": "https://api-jp.libreview.io",
        "LA": "https://api-la.libreview.io",
    }

    def __init__(self, username: str, password: str, region: str = "EU") -> None:
        self.username = username
        self.password = password
        self.region = region.upper()
        self.base_url = self.BASE_URLS.get(self.region, self.BASE_URLS["EU"])
        self._token: str | None = None
        self._user_id: str | None = None
        self._patient_id: str | None = None
        self._http = httpx.AsyncClient(timeout=30.0)

    def _get_headers(self, authenticated: bool = False) -> dict[str, str]:
        """Get headers for LibreLinkUp API requests."""
        headers = {
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json;charset=UTF-8",
            "version": "4.16.0",
            "product": "llu.ios",
            "accept-encoding": "gzip",
        }
        if authenticated and self._token:
            headers["Authorization"] = f"Bearer {self._token}"
            if self._user_id:
                # Add SHA256 hashed account-id
                account_id = hashlib.sha256(self._user_id.encode()).hexdigest()
                headers["account-id"] = account_id
        return headers

    async def _ensure_authenticated(self) -> None:
        """Authenticate if not already authenticated."""
        if self._token is None:
            await self._login()
        if self._patient_id is None:
            await self._get_patient_id()

    async def _login(self) -> None:
        """Authenticate with LibreLinkUp and store the auth token."""
        logger.info(f"Logging in to LibreLinkUp ({self.region})...")

        url = f"{self.base_url}/llu/auth/login"
        resp = await self._http.post(
            url,
            json={"email": self.username, "password": self.password},
            headers=self._get_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

        logger.info(f"Login response status: {data.get('status')}")

        # Check for redirect (region mismatch)
        if data.get("status") == 2 and data.get("data", {}).get("redirect"):
            new_region = data["data"]["region"]
            logger.info(f"Redirecting to region: {new_region}")
            self.base_url = self.BASE_URLS.get(new_region.upper(), self.base_url)
            # Retry login with new region
            url = f"{self.base_url}/llu/auth/login"
            resp = await self._http.post(
                url,
                json={"email": self.username, "password": self.password},
                headers=self._get_headers(),
            )
            resp.raise_for_status()
            data = resp.json()

        # Check for terms acceptance requirement
        if data.get("status") == 4:
            logger.warning("Terms of use acceptance required.")
            raise RuntimeError("Terms of use acceptance required in LibreLinkUp app")

        # Extract auth ticket and user ID
        auth_data = data.get("data", {})
        auth_ticket = auth_data.get("authTicket", {})
        self._token = auth_ticket.get("token")

        # Get user ID for account-id header
        user_data = auth_data.get("user", {})
        self._user_id = user_data.get("id")

        if not self._token:
            logger.error(f"Login failed. Response: {data}")
            raise RuntimeError("Failed to get auth token from LibreLinkUp")

        logger.info("Successfully logged in to LibreLinkUp")

    async def _get_patient_id(self) -> None:
        """Get the first patient connection ID."""
        url = f"{self.base_url}/llu/connections"
        resp = await self._http.get(
            url,
            headers=self._get_headers(authenticated=True),
        )

        logger.info(f"Connections response status: {resp.status_code}")
        if resp.status_code != 200:
            logger.info(f"Connections response body: {resp.text[:500]}")

        resp.raise_for_status()
        data = resp.json()

        connections = data.get("data", [])
        if connections:
            self._patient_id = connections[0]["patientId"]
            logger.info(f"Found patient ID: {self._patient_id}")
        else:
            logger.warning("No patient connections found.")

    async def get_current(self) -> GlucoseEntry | None:
        """Get the most recent glucose reading."""
        entries = await self.get_entries(count=1)
        return entries[0] if entries else None

    async def get_entries(self, count: int = 10) -> list[GlucoseEntry]:
        """Get recent glucose readings from LibreLinkUp."""
        await self._ensure_authenticated()

        if not self._patient_id:
            return []

        url = f"{self.base_url}/llu/connections/{self._patient_id}/graph"
        resp = await self._http.get(
            url,
            headers=self._get_headers(authenticated=True),
        )
        resp.raise_for_status()
        data = resp.json()["data"]

        entries = []
        graph_data = data.get("graphData", [])

        for item in graph_data[-count:]:
            trend_value = item.get("TrendArrow", item.get("trend", 3))
            trend = TREND_MAP.get(trend_value, Trend.UNKNOWN)

            ts_str = item.get("Timestamp", item.get("FactoryTimestamp", item.get("timestamp", "")))
            try:
                timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                timestamp = datetime.now(timezone.utc)

            value = item.get("ValueInMgPerDl", item.get("Value", item.get("value", 0)))

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
