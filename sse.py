"""Server-Sent-Events (SSE) Subscriber für WLWBX /events."""
from __future__ import annotations

import asyncio
import logging
from json import loads as json_loads
from typing import Any

import aiohttp

from .api import WlwbxApiClient

_LOGGER = logging.getLogger(__name__)

# Events mit leerem data-Feld: zugehörigen GET-Endpoint neu abrufen
# (siehe OpenAPI: "relatedGetApi")
EVENT_TO_POLL = {
    "chargingStateUpdate": ("state", "/charging/state"),
    "lastStartedSessionUpdate": ("session", "/charging/last-started-session"),
    "chargingLimitsUpdate": ("limits", "/charging/limits"),
    "chargingUserLimitCurrentUpdate": (
        "user_limit_current", "/charging/user-limit-current",
    ),
    "chargingFreeChargingUpdate": ("free_charging", "/charging/free-charging"),
    "errorsUpdate": ("errors", "/system/errors"),
    "energyMeterUpdate": ("energy_meter", "/system/energy-meter"),
    "deviceStateUpdate": ("device_state", "/system/device-state"),
    "electronicTypeplateUpdate": ("typeplate", "/system/electronic-typeplate"),
    "updateInfoUpdate": ("update_info", "/system/update/info"),
}


class WlwbxEventSubscriber:
    """Hält den /events-Stream offen und pusht Updates in den Coordinator."""

    def __init__(self, api: WlwbxApiClient, coordinator) -> None:
        self._api = api
        self._coordinator = coordinator
        self._stop = False
        self._session: aiohttp.ClientSession | None = None
        self._backoff = 5

    async def start(self) -> None:
        """Endlosschleife: Stream konsumieren, bei Abbruch neu verbinden."""
        while not self._stop:
            try:
                await self._stream_once()
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("SSE-Stream abgebrochen: %s", err)
            if self._stop:
                break
            # Reconnect mit Backoff (5s -> 10s -> ... max 300s)
            await asyncio.sleep(self._backoff)
            self._backoff = min(self._backoff * 2, 300)

    async def astop(self) -> None:
        """Stream sauber beenden (beim Entladen der Integration)."""
        self._stop = True
        if self._session and not self._session.closed:
            await self._session.close()

    async def _stream_once(self) -> None:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(ssl=self._api.verify_ssl)
            self._session = aiohttp.ClientSession(connector=connector)

        if self._api.token is None:
            await self._api.async_login()

        async with self._session.get(
            f"{self._api.base_url}/events",
            headers={"Authorization": f"Bearer {self._api.token}"},
            # Kein Gesamt-Timeout; aber Abbruch, wenn >120 s nichts kommt
            timeout=aiohttp.ClientTimeout(total=None, sock_read=120),
        ) as resp:
            if resp.status == 401:
                # Token abgelaufen -> neu einloggen, Reconnect folgt
                await self._api.async_login()
                raise RuntimeError("SSE: Token war abgelaufen, neu eingeloggt")
            resp.raise_for_status()
            self._backoff = 5  # Verbindung steht -> Backoff zurücksetzen

            event_name: str | None = None
            data_lines: list[str] = []

            async for raw in resp.content:
                if self._stop:
                    return
                line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                if line == "":
                    # Leerzeile = Ende einer SSE-Nachricht
                    if event_name:
                        await self._handle_event(event_name, "\n".join(data_lines))
                    event_name, data_lines = None, []
                elif line.startswith("event:"):
                    event_name = line[len("event:"):].strip()
                elif line.startswith("data:"):
                    data_lines.append(line[len("data:"):].strip())
                # Kommentar-/Heartbeat-Zeilen (":"-Prefix) ignorieren

    async def _handle_event(self, event: str, data: str) -> None:
        updates: dict[str, Any] = {}

        if event == "chargingCurvePointAppend":
            # Datenpunkt kommt direkt im Event mit -> an Kurve anhängen
            try:
                point = json_loads(data)
            except ValueError:
                return
            curve = dict(self._coordinator.data.get("charging_curve") or {})
            points = list(curve.get("curvePoints") or [])
            points.append(point)
            curve["curvePoints"] = points
            if point.get("sessionId") is not None:
                curve["sessionId"] = point["sessionId"]
            updates["charging_curve"] = curve

        elif event == "updateProgressUpdate":
            try:
                updates["update_progress"] = json_loads(data)
            except ValueError:
                return

        elif event in EVENT_TO_POLL:
            key, path = EVENT_TO_POLL[event]
            try:
                updates[key] = await self._api.async_get(path)
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("SSE: %s nicht abrufbar: %s", path, err)
                return

        else:
            return  # Event ist für uns nicht relevant

        if updates:
            self._coordinator.async_set_updated_data(
                {**self._coordinator.data, **updates}
            )
