"""Async REST client for the WLWBX API v2."""
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

def _build_base_url(host: str) -> str:
    """Scheme ergänzen, falls nur IP/Hostname eingegeben wurde."""
    if not host.startswith(("http://", "https://")):
        host = "http://" + host
    return host.rstrip("/") + "/api/v2"

class WlwbxApiError(Exception):
    """Base exception."""


class WlwbxAuthError(WlwbxApiError):
    """Authentication failed (401/403)."""


class WlwbxApiClient:
    """Wraps the wallbox REST API with automatic JWT login/refresh."""

    def __init__(self, host: str, username: str, password: str, verify_ssl: bool = True) -> None:
        self._base = host.rstrip("/") + "/api/v2"
        self._username = username
        self._password = password
        self._verify_ssl = verify_ssl
        self._token: str | None = None
        self._session: aiohttp.ClientSession | None = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(ssl=self._verify_ssl)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=10),
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
        self._token = None

    async def async_login(self) -> str:
        """POST /jwt/login (form-urlencoded), token from Authorization header."""
        session = await self._ensure_session()
        async with session.post(
            f"{self._base}/jwt/login",
            data={"user": self._username, "pass": self._password},
        ) as resp:
            if resp.status in (400, 401):
                raise WlwbxAuthError(
                    f"Login fehlgeschlagen ({resp.status}) – "
                    "Pass Penalty-Timer läuft ggf. noch."
                )
            resp.raise_for_status()
            auth = resp.headers.get("Authorization")
            if not auth:
                raise WlwbxAuthError("Kein Bearer-Token in der Login-Antwort")
            self._token = auth.removeprefix("Bearer ").strip()
            return self._token

    async def _request(
        self, method: str, path: str, json: dict[str, Any] | None = None
    ) -> Any:
        session = await self._ensure_session()
        if self._token is None:
            await self.async_login()

        async def _do() -> aiohttp.ClientResponse:
            return session.request(
                method,
                f"{self._base}{path}",
                json=json,
                headers={"Authorization": f"Bearer {self._token}"},
            )

        resp = await _do()
        # Token abgelaufen -> einmal neu einloggen und wiederholen
        if resp.status == 401:
            await resp.release()
            await self.async_login()
            resp = await _do()
        try:
            if resp.status == 403:
                raise WlwbxAuthError(
                    f"{method} {path}: 403 – Rolle '{self._username}' nicht berechtigt"
                )
            if resp.status == 404:
                raise WlwbxApiError(f"{path} ist auf dieser Wallbox nicht implementiert")
            if resp.status == 204:
                return None
            resp.raise_for_status()
            if not resp.content_type.startswith("application/json"):
                text = await resp.text()
                return {"value": text} if text else None
            return await resp.json()
        finally:
            if not resp.closed:
                resp.release()

    # --- GET helpers -------------------------------------------------
    async def async_get(self, path: str) -> Any:
        return await self._request("GET", path)

    async def async_put(self, path: str, body: dict[str, Any]) -> None:
        await self._request("PUT", path, json=body)

    # --- convenience methods -----------------------------------------
    async def async_get_charging_state(self) -> str:
        return (await self.async_get("/charging/state")).get("value")

    async def async_get_last_session(self) -> dict[str, Any] | None:
        return await self.async_get("/charging/last-started-session")

    async def async_get_limits(self) -> dict[str, Any]:
        return await self.async_get("/charging/limits")

    async def async_get_user_limit_current(self) -> int:
        return (await self.async_get("/charging/user-limit-current")).get("value")

    async def async_set_user_limit_current(self, amps: int) -> None:
        await self.async_put("/charging/user-limit-current", {"value": int(amps)})

    async def async_get_direct_authorization(self) -> str:
        return (await self.async_get("/charging/direct-authorization")).get("value")

    async def async_set_direct_authorization(self, allow: bool) -> None:
        await self.async_put(
            "/charging/direct-authorization",
            {"value": "allow" if allow else "deny"},
        )

    async def async_get_free_charging(self) -> bool:
        return (await self.async_get("/charging/free-charging")).get("value") is True

    async def async_set_free_charging(self, enabled: bool) -> None:
        await self.async_put("/charging/free-charging", {"value": enabled})

    async def async_get_update_info(self) -> dict[str, Any] | None:
        return await self.async_get("/system/update/info")

    async def async_get_update_progress(self) -> dict[str, Any] | None:
        return await self.async_get("/system/update/progress")

    async def async_download_update(self) -> None:
        """POST /system/update/download – Update-Datei vom Backend laden."""
        await self._request("POST", "/system/update/download")

    async def async_exec_update(self) -> None:
        """POST /system/update/exec – installiert eine vorhandene Update-Datei."""
        await self._request("POST", "/system/update/exec")