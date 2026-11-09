"""Buttons for WLWBX (Direct Authorization = einmalige Freigabe)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
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
    async_add_entities(
        [
            DirectAuthorizationButton(coordinator, entry, api, allow=True),
            DirectAuthorizationButton(coordinator, entry, api, allow=False),
            ErrorResetButton(coordinator, entry, api),
        ]
    )


class DirectAuthorizationButton(WlwbxEntity, ButtonEntity):
    """Einmalige Lade-Freigabe bzw. -Verweigerung via /charging/direct-authorization.

    Kein Schalter: der Zustand der Box ist flüchtig (allowed -> unknown),
    PUT löst nur eine einmalige Aktion aus.
    """

    def __init__(self, coordinator, entry, api, allow: bool) -> None:
        super().__init__(coordinator, entry, "auth_allow" if allow else "auth_deny")
        self._api = api
        self._allow = allow
        self._attr_name = (
            "Wallbox Laden erlauben" if allow else "Wallbox Laden verweigern"
        )
        self._attr_icon = "mdi:play" if allow else "mdi:stop"

    @property
    def available(self) -> bool:
        # Endpunkt nicht implementiert (404) -> Entity ausblenden
        return self.coordinator.data.get("direct_authorization") is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        # Aktuellen Freigabe-Zustand der Box als Attribut mitliefern
        value = (self.coordinator.data.get("direct_authorization") or {}).get("value")
        return {"authorization_state": value}

    async def async_press(self) -> None:
        await self._api.async_set_direct_authorization(self._allow)
        await self.coordinator.async_request_refresh()


class ErrorResetButton(WlwbxEntity, ButtonEntity):
    """Fehlerliste der Wallbox löschen via DELETE /system/errors.

    Löscht die Fehlerhistorie (passive Fehler); aktive Fehler bleiben
    bestehen, solange ihre Ursache besteht. Die Box sendet danach das
    SSE-Event errorsUpdate -> Coordinator aktualisiert automatisch.
    """

    _attr_icon = "mdi:notification-clear-all"

    def __init__(self, coordinator, entry, api) -> None:
        super().__init__(coordinator, entry, "error_reset")
        self._api = api
        self._attr_name = "Wallbox Fehler löschen"

    @property
    def available(self) -> bool:
        return self.coordinator.data.get("errors") is not None

    async def async_press(self) -> None:
        await self._api.async_delete_errors()
        await self.coordinator.async_request_refresh()
