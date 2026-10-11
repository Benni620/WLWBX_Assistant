"""Update entity for WLWBX firmware updates."""
from __future__ import annotations

from typing import Any

from homeassistant.components.update import (
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import WlwbxEntity
from .const import DOMAIN

# UpdateProgress.state -> HA in_progress
INSTALLING_STATES = {"installing", "rebooting"}
DOWNLOADING_STATES = {"downloadingFromBackend"}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    store = hass.data[DOMAIN][entry.entry_id]
    coordinator, api = store["coordinator"], store["api"]
    async_add_entities([WlwbxUpdateEntity(coordinator, entry, api)])


class WlwbxUpdateEntity(WlwbxEntity, UpdateEntity):
    """Firmware-Update der Wallbox via /system/update/*."""

    _attr_name = "Wallbox Firmware"
    _attr_title = "Wallbox Firmware"

    def __init__(self, coordinator, entry, api) -> None:
        super().__init__(coordinator, entry, "firmware")
        self._api = api
        self._attr_supported_features = (
            UpdateEntityFeature.INSTALL
            | UpdateEntityFeature.PROGRESS
        )

    def _info(self) -> dict[str, Any]:
        return self.coordinator.data.get("update_info") or {}

    def _progress(self) -> dict[str, Any]:
        return self.coordinator.data.get("update_progress") or {}

    @property
    def installed_version(self) -> str | None:
        # Aktuell installierte Version: aus lastUpdate, sonst aus dem Typeplate
        last = self._info().get("lastUpdate")
        if last and last.get("version"):
            return last["version"]
        typeplate = self.coordinator.data.get("typeplate") or {}
        return typeplate.get("bundleVersion")

    @property
    def latest_version(self) -> str | None:
        # Ein Update ist nur "verfügbar", wenn die Box es auch lokal heruntergeladen hat
        progress_state = self._progress().get("state")
        if progress_state in ("pending", "installing", "rebooting"):
            running = self._info().get("runningUpdate") or {}
            return running.get("version") or self._info().get("availableUpdate", {}).get("version")
        if progress_state == "postponed":
            return self._info().get("availableUpdate", {}).get("version")
        return (self._info().get("availableUpdate") or {}).get("version")

    @property
    def release_summary(self) -> str | None:
        info = self._info()
        source = (
            info.get("runningUpdate") or info.get("availableUpdate") or {}
        )
        changelog = source.get("changelog")
        return changelog

    @property
    def in_progress(self) -> bool | int:
        state = self._progress().get("state")
        if state in INSTALLING_STATES or state in DOWNLOADING_STATES:
            return self._progress().get("progress", 0)
        return False

    async def async_install(self, version: str | None, backup: bool, **kwargs: Any) -> None:
        """Installations-Flow: Download vom Backend (falls nötig) + Installation starten."""
        progress_state = self._progress().get("state")
        if progress_state == "readyToDownload":
            await self._api.async_download_update()
        await self._api.async_exec_update()
        # Während der Installation (inkl. Reboot) häufiger aktualisieren
        await self.coordinator.async_request_refresh()