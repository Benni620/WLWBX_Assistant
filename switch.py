"""Switches for WLWBX."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .entity import WlwbxEntity
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    store = hass.data[DOMAIN][entry.entry_id]
    coordinator, api = store["coordinator"], store["api"]
    async_add_entities(
        [
            ChargingAllowedSwitch(coordinator, entry, api),
            FreeChargingSwitch(coordinator, entry, api),
        ]
    )


class ChargingAllowedSwitch(WlwbxEntity, SwitchEntity):
    """Laden erlauben/sperren via /charging/direct-authorization."""

    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator, entry, api) -> None:
        super().__init__(coordinator, entry, "charging_allowed")
        self._api = api
        self._attr_name = "Wallbox Laden erlaubt"

    @property
    def is_on(self) -> bool | None:
        value = (self.coordinator.data.get("direct_authorization") or {}).get("value")
        return None if value == "unknown" else value == "allowed"

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._api.async_set_direct_authorization(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._api.async_set_direct_authorization(False)
        await self.coordinator.async_request_refresh()


class FreeChargingSwitch(WlwbxEntity, SwitchEntity):
    """Freies Laden (ohne Autorisierung) via /charging/free-charging."""

    _attr_icon = "mdi:cash-off"

    def __init__(self, coordinator, entry, api) -> None:
        super().__init__(coordinator, entry, "free_charging")
        self._api = api
        self._attr_name = "Wallbox Freies Laden"

    @property
    def is_on(self) -> bool | None:
        value = (self.coordinator.data.get("free_charging") or {}).get("value")
        return value is True

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._api.async_set_free_charging(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._api.async_set_free_charging(False)
        await self.coordinator.async_request_refresh()