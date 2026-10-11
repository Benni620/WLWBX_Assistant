"""Shared entity base class."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER


class WlwbxEntity(CoordinatorEntity):
    """Base entity: one device per wallbox, data via coordinator."""

    def __init__(self, coordinator, entry, kind: str) -> None:
        super().__init__(coordinator)
        self._kind = kind
        serial = (coordinator.data.get("typeplate") or {}).get(
            "serialNumber", entry.entry_id
        )
        self._attr_unique_id = f"{serial}_{kind}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name="WLWBX Wallbox",
            manufacturer=(coordinator.data.get("typeplate") or {}).get(
                "brand", MANUFACTURER
            ),
            model=(coordinator.data.get("typeplate") or {}).get("partNumber"),
            sw_version=(coordinator.data.get("typeplate") or {}).get("bundleVersion"),
        )