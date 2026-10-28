"""Async REST client for the WLWBX API v2."""
import logging
from json import loads as json_loads
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

    def __init__(
        self, host: str, username: str, password: str, verify_ssl: bool = True
    ) -> None:
        self._base = _build_base_url(host)
        self._username = username
        self._password = password
        self._verify_ssl = verify_ssl
        self._token: str | None = None
        self._session: aiohttp.ClientSession | None = None
        self._locales: dict[str, dict[str, Any]] = {}

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

    # --- für SSE-Subscriber zugängliche Interna ----------------------
    @property
    def base_url(self) -> str:
        """Basis-URL inkl. /api/v2 (für z.B. /events-Stream)."""
        return self._base

    @property
    def token(self) -> str | None:
        """Aktueller Bearer-Token (None = nicht eingeloggt)."""
        return self._token

    @property
    def verify_ssl(self) -> bool:
        return self._verify_ssl

    @property
    def _origin(self) -> str:
        """URL ohne /api/v2 (für statische WebUI-Dateien wie /locales/...)."""
        return self._base.removesuffix("/api/v2")

    async def async_get_locale(self, lang: str = "de") -> dict[str, Any] | None:
        """Lädt (und cached) die WebUI-Übersetzungsdatei locales/default/<lang>.json.

        Nicht Teil der OpenAPI-Spec; enthält u.a. faultManagement.errorCause
        mit den DTC-Beschreibungen.
        """
        cached = self._locales.get(lang)
        if cached is not None:
            return cached
        session = await self._ensure_session()
        url = f"{self._origin}/locales/default/{lang}.json"
        async with session.get(url) as resp:
            if resp.status != 200:
                _LOGGER.debug("Locale %s nicht verfügbar: HTTP %s", lang, resp.status)
                return None
            try:
                data = await resp.json()
            except ValueError:
                return None
            self._locales[lang] = data
            return data

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

    async def _attempt(
        self, method: str, path: str, json: dict[str, Any] | None = None
    ) -> tuple[int, bytes]:
        """Führt einen Request aus und liefert (status, roher Body)."""
        session = await self._ensure_session()
        async with session.request(
            method,
            f"{self._base}{path}",
            json=json,
            headers={"Authorization": f"Bearer {self._token}"},
        ) as resp:
            return resp.status, await resp.read()

    async def _request(
        self, method: str, path: str, json: dict[str, Any] | None = None
    ) -> Any:
        if self._token is None:
            await self.async_login()

        status, raw = await self._attempt(method, path, json)

        # Token abgelaufen -> einmal neu einloggen und wiederholen
        if status == 401:
            await self.async_login()
            status, raw = await self._attempt(method, path, json)

        if status == 403:
            raise WlwbxAuthError(
                f"{method} {path}: 403 – Rolle '{self._username}' nicht berechtigt"
            )
        if status == 404:
            detail = raw[:200].decode(errors="replace")
            raise WlwbxApiError(
                f"{method} {path}: 404 – "
                f"nicht implementiert? Body: {detail or '<leer>'}"
            )
        if status >= 400:
            detail = raw[:200].decode(errors="replace")
            raise WlwbxApiError(
                f"{method} {path}: HTTP {status} – Body: {detail or '<leer>'}"
            )

        if status == 204 or not raw:
            return None
        try:
            return json_loads(raw)
        except ValueError:
            return None

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
        return (await self.async_get("/charging/free-charging")).get("enabled") is True

    async def async_set_free_charging(self, enabled: bool) -> None:
        # Achtung: Feld heißt "enabled", nicht "value" (OpenAPI-Schema "Enabled")
        await self.async_put("/charging/free-charging", {"enabled": bool(enabled)})

    async def async_get_update_info(self) -> dict[str, Any] | None:
        return await self.async_get("/system/update/info")

    async def async_delete_errors(self) -> None:
        """DELETE /system/errors – Fehlerliste löschen (passive Fehler)."""
        await self._request("DELETE", "/system/errors")

    async def async_get_update_progress(self) -> dict[str, Any] | None:
        return await self.async_get("/system/update/progress")

    async def async_download_update(self) -> None:
        """POST /system/update/download – Update-Datei vom Backend laden."""
        await self._request("POST", "/system/update/download")

    async def async_exec_update(self) -> None:
        """POST /system/update/exec – installiert eine vorhandene Update-Datei."""
        await self._request("POST", "/system/update/exec")