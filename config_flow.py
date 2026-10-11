"""Config flow for WLWBX."""
import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .api import WlwbxApiClient, WlwbxApiError
from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME, default="technician"): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def _test_connection(hass: HomeAssistant, data: dict[str, str]) -> None:
    """Raise on connection or auth failure."""
    client = WlwbxApiClient(
        data[CONF_HOST], data[CONF_USERNAME], data[CONF_PASSWORD]
    )
    try:
        await client.async_login()
        # Ein lesender Aufruf gegen die Rolle prüfen
        await client.async_get_charging_state()
    except WlwbxApiError:
        # 404 je nach Modell ok – Login hat funktioniert
        pass
    finally:
        await client.close()


class WlwbxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the WLWBX config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await _test_connection(self.hass, user_input)
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unerwarteter Fehler im Config Flow")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Wallbox {user_input[CONF_HOST]}", data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )