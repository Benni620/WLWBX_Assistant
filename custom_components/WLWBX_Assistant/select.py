"""Select for WLWBX (socket-outlet lock activation)."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import WlwbxApiError
from .entity import WlwbxEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# API-Werte (SocketOutletLockActivation-Enum)
LOCK_ACTIVATION_OPTIONS = {
    "whenCableDetected": "Bei Kabelerkennung",
    "duringCharging": "Während des Ladens",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    store = hass.data[DOMAIN][entry.entry_id]
    coordinator, api = store["coordinator"], store["api"]
    async_add_entities([SocketOutletLockActivation(coordinator, entry, api)])


class SocketOutletLockActivation(WlwbxEntity, SelectEntity):
    """Verriegelungsmodus der Steckdose via PUT /system/socket-outlet.

    Steckdose mit Verriegelung (Typ 2 mit Aktor) verriegelt entweder,
    sobald ein Kabel erkannt wird, oder erst während des Ladens. Nur
    ausgestattet bei Boxen mit verriegelbarer Steckdose (sonst 404).
    """

    _attr_icon = "mdi:lock-cog"
    _attr_name = "Wallbox Steckdosenverriegelung"

    def __init__(self, coordinator, entry, api) -> None:
        super().__init__(coordinator, entry, "socket_outlet_lock")
        self._api = api

    @property
    def available(self) -> bool:
        # Endpunkt nicht implementiert (404) -> Entity ausblenden
        return self.coordinator.data.get("socket_outlet") is not None

    @property
    def options(self) -> list[str]:
        return list(LOCK_ACTIVATION_OPTIONS.values())

    @property
    def current_option(self) -> str | None:
        raw = (self.coordinator.data.get("socket_outlet") or {}).get("lockActivation")
        return LOCK_ACTIVATION_OPTIONS.get(raw)

    async def async_select_option(self, option: str) -> None:
        raw = next(
            (k for k, v in LOCK_ACTIVATION_OPTIONS.items() if v == option), None
        )
        if raw is None:
            return
        try:
            await self._api.async_set_socket_outlet(raw)
        except WlwbxApiError as err:
            _LOGGER.warning("Speichern des Verriegelungsmodus fehlgeschlagen: %s", err)
            return
        await self.coordinator.async_request_refresh()
