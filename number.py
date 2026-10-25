"""Number entities for WLWBX (Stromlimit)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import WlwbxEntity
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    store = hass.data[DOMAIN][entry.entry_id]
    coordinator, api = store["coordinator"], store["api"]
    async_add_entities([UserLimitCurrent(coordinator, entry, api)])


class UserLimitCurrent(WlwbxEntity, NumberEntity):
    """Max. Ladestrom (A) via /charging/user-limit-current."""

    _attr_icon = "mdi:current-ac"
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_mode = "box"
    _attr_native_min_value = 6.0
    _attr_native_step = 1.0

    def __init__(self, coordinator, entry, api) -> None:
        super().__init__(coordinator, entry, "user_limit_current")
        self._api = api
        self._attr_name = "Wallbox Max. Ladestrom"

    @property
    def native_max_value(self) -> float:
        # Dynamisch aus /charging/limits; maxCurrent kann 0 sein
        # (z.B. wenn nicht geladen wird) -> dann Fallback 32 A.
        limits = self.coordinator.data.get("limits") or {}
        max_current = limits.get("maxCurrent")
        if isinstance(max_current, (int, float)) and max_current >= self._attr_native_min_value:
            return float(max_current)
        return 32.0

    @property
    def available(self) -> bool:
        # Endpunkt nicht implementiert (404) -> Entity ausblenden
        return self.coordinator.data.get("user_limit_current") is not None

    @property
    def native_value(self) -> float | None:
        value = (self.coordinator.data.get("user_limit_current") or {}).get("value")
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        await self._api.async_set_user_limit_current(int(value))
        await self.coordinator.async_request_refresh()