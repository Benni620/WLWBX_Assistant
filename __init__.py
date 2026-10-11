"""Support for WLWBX wallboxes."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import WlwbxApiClient, WlwbxApiError
from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.NUMBER, Platform.SENSOR, Platform.SWITCH, Platform.UPDATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WLWBX from a config entry."""
    api = WlwbxApiClient(
        entry.data[CONF_HOST], entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]
    )

    # Mapping API-Endpoint -> Schlüssel im Coordinator-Dict.
    # Mit None markierte Calls schlagen optional fehl (z.B. 404 je nach Modell).
    POLL_PATHS = {
        "state": "/charging/state",
        "session": "/charging/last-started-session",
        "limits": "/charging/limits",
        "user_limit_current": "/charging/user-limit-current",
        "direct_authorization": "/charging/direct-authorization",
        "free_charging": "/charging/free-charging",
        "lifetime": "/charging/lifetime-stats",
        "energy_meter": "/system/energy-meter",
        "device_state": "/system/device-state",
        "typeplate": "/system/electronic-typeplate",
        "errors": "/system/errors",
        "update_info": "/system/update/info",
        "update_progress": "/system/update/progress",
    }
    REQUIRED = {"state", "limits", "direct_authorization"}

    async def async_update_data() -> dict:
        data: dict = {}
        for key, path in POLL_PATHS.items():
            try:
                data[key] = await api.async_get(path)
            except WlwbxApiError as err:
                if key in REQUIRED:
                    raise UpdateFailed(str(err)) from err
                _LOGGER.debug("%s nicht verfügbar: %s", path, err)
                data[key] = None
        return data

    coordinator = DataUpdateCoordinator(
        hass,
        logger=_LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except UpdateFailed as err:
        await api.close()
        raise ConfigEntryNotReady(str(err)) from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }
    await hass.config_entries.async_forward_platform_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
    if unload_ok:
        store = hass.data[DOMAIN].pop(entry.entry_id)
        await store["api"].close()
    return unload_ok