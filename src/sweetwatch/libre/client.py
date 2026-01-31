"""LibreLinkUp API client."""

import httpx


class LibreLinkUpClient:
    """Client for the LibreLinkUp API."""

    BASE_URLS: dict[str, str] = {
        "EU": "https://api-eu.libreview.io",
        "US": "https://api-us.libreview.io",
    }

    def __init__(self, username: str, password: str, region: str = "EU") -> None:
        self.username = username
        self.password = password
        self.base_url = self.BASE_URLS.get(region.upper(), self.BASE_URLS["EU"])
        self._token: str | None = None
        self._http = httpx.AsyncClient(base_url=self.base_url)

    async def login(self) -> None:
        """Authenticate with LibreLinkUp and store the auth token."""
        resp = await self._http.post(
            "/llu/auth/login",
            json={"email": self.username, "password": self.password},
            headers={"Content-Type": "application/json", "product": "llu.android", "version": "4.7.0"},
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["data"]["authTicket"]["token"]

    async def get_connections(self) -> list[dict]:
        """Get patient connections."""
        resp = await self._http.get(
            "/llu/connections",
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()["data"]

    async def get_graph_data(self, patient_id: str) -> dict:
        """Get CGM graph data for a patient."""
        resp = await self._http.get(
            f"/llu/connections/{patient_id}/graph",
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()["data"]

    def _auth_headers(self) -> dict[str, str]:
        if not self._token:
            raise RuntimeError("Not authenticated. Call login() first.")
        return {
            "Authorization": f"Bearer {self._token}",
            "product": "llu.android",
            "version": "4.7.0",
        }

    async def close(self) -> None:
        await self._http.aclose()
