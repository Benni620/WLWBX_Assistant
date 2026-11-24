"""Select for WLWBX (socket-outlet lock activation)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import WlwbxApiError
from .entity import WlwbxEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# API-Werte (SocketOutletLockActivation-Enum);
# Bezeichnungen kommen aus den WebUI-locales (socketOutlet.activate*),
# Fallbacks unten greifen nur, wenn keine Locale-Datei geladen ist.
_LOCK_ACTIVATION_FALLBACKS = {
    "whenCableDetected": "Bei verbundenem Ladekabel",
    "duringCharging": "Während des aktiven Ladevorgangs",
}
_LOCK_ACTIVATION_LOCALE_KEYS = {
    "whenCableDetected": "activateWhenCableDetected",
    "duringCharging": "activateDuringCharging",
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
    ausgestattet bei Boxen mit verriegelbarer Steckdose (sonst 404 bzw.
    lockStatus notEquipped) -> Entity wird ausgeblendet.
    """

    _attr_icon = "mdi:lock-cog"
    _attr_name = "Wallbox Steckdosenverriegelung"

    def __init__(self, coordinator, entry, api) -> None:
        super().__init__(coordinator, entry, "socket_outlet_lock")
        self._api = api

    def _locale(self, *path) -> str | None:
        """Wert aus den WebUI-locales (Sprache folgt HA-Sprache)."""
        locales = self.coordinator.data.get("locales") or {}
        node: Any = next(iter(locales.values()), None) or {}
        for part in path:
            if not isinstance(node, dict):
                return None
            node = node.get(part)
            if node is None:
                return None
        return node

    def _options_map(self) -> dict[str, str]:
        """Mapping API-Wert -> lokalisierte Bezeichnung."""
        return {
            raw: self._locale("socketOutlet", key)
            or _LOCK_ACTIVATION_FALLBACKS[raw]
            for raw, key in _LOCK_ACTIVATION_LOCALE_KEYS.items()
        }

    @property
    def available(self) -> bool:
        # Kabel-Variante ohne verriegelbare Steckdose ausblenden
        outlet = self.coordinator.data.get("socket_outlet") or {}
        return outlet.get("lockStatus") not in (None, "notEquipped")

    @property
    def options(self) -> list[str]:
        return list(self._options_map().values())

    @property
    def current_option(self) -> str | None:
        raw = (self.coordinator.data.get("socket_outlet") or {}).get(
            "lockActivation"
        )
        return self._options_map().get(raw)

    async def async_select_option(self, option: str) -> None:
        raw = next(
            (k for k, v in self._options_map().items() if v == option), None
        )
        if raw is None:
            return
        try:
            await self._api.async_set_socket_outlet(raw)
        except WlwbxApiError as err:
            _LOGGER.warning("Speichern des Verriegelungsmodus fehlgeschlagen: %s", err)
            return
        await self.coordinator.async_request_refresh()
