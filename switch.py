"""Switches for WLWBX."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import WlwbxEntity
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    store = hass.data[DOMAIN][entry.entry_id]
    coordinator, api = store["coordinator"], store["api"]
    async_add_entities([FreeChargingSwitch(coordinator, entry, api)])


class FreeChargingSwitch(WlwbxEntity, SwitchEntity):
    """Freies Laden (ohne Autorisierung) via /charging/free-charging."""

    _attr_icon = "mdi:cash-off"

    def __init__(self, coordinator, entry, api) -> None:
        super().__init__(coordinator, entry, "free_charging")
        self._api = api
        self._attr_name = "Wallbox Freies Laden"

    @property
    def available(self) -> bool:
        # Endpunkt nicht implementiert (404) -> Entity ausblenden
        return self.coordinator.data.get("free_charging") is not None

    @property
    def is_on(self) -> bool | None:
        value = (self.coordinator.data.get("free_charging") or {}).get("enabled")
        return value is True

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._api.async_set_free_charging(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._api.async_set_free_charging(False)
        await self.coordinator.async_request_refresh()