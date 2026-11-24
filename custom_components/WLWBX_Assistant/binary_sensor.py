"""Binary sensors for WLWBX, derived from /charging/state."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import WlwbxEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Alle Zustände, in denen ein Fahrzeug physisch verbunden ist
CONNECTED_STATES = {
    "VehicleConnected",
    "Authorizing",
    "Charging",
    "ISOCharging",
    "Paused",
    "ChargingComplete",
    "Error",
}
# Wirklich ladende Zustände (HLC-Laden zählt mit)
CHARGING_STATES = {"Charging", "ISOCharging"}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[BinarySensorEntity] = [
        WlwbxBinarySensor(
            coordinator, entry, "vehicle_connected", "Fahrzeug verbunden",
            device_class=BinarySensorDeviceClass.PLUG,
        ),
        WlwbxBinarySensor(
            coordinator, entry, "is_charging", "Wird geladen",
            icon="mdi:ev-station",
        ),
        WlwbxBinarySensor(
            coordinator, entry, "charging_error", "Ladefehler",
            device_class=BinarySensorDeviceClass.PROBLEM,
        ),
    ]
    async_add_entities(entities)


class WlwbxBinarySensor(WlwbxEntity, BinarySensorEntity):
    def __init__(
        self, coordinator, entry, kind: str, name: str,
        device_class=None, icon=None,
    ) -> None:
        super().__init__(coordinator, entry, kind)
        self._attr_name = f"Wallbox {name}"
        self._attr_device_class = device_class
        self._attr_icon = icon

    def _raw(self) -> str | None:
        """Roher Charging-State der Box (None, wenn Endpoint fehlt)."""
        if self.coordinator.data.get("state") is None:
            return None
        return (self.coordinator.data.get("state") or {}).get("value")

    @property
    def available(self) -> bool:
        return self.coordinator.data.get("state") is not None

    @property
    def is_on(self) -> bool | None:
        raw = self._raw()
        if raw is None:
            return None
        if self._kind == "vehicle_connected":
            return raw in CONNECTED_STATES
        if self._kind == "is_charging":
            return raw in CHARGING_STATES
        if self._kind == "charging_error":
            return raw == "Error"
        return None
