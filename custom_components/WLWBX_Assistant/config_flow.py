"""Config flow for WLWBX."""
import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .api import WlwbxApiClient, WlwbxApiError, WlwbxAuthError
from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_VERIFY_SSL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME, default="technician"): str,
        vol.Required(CONF_PASSWORD): str,
        # Bei selbst signiertem Zertifikat (https) standardmäßig aus
        vol.Optional(CONF_VERIFY_SSL, default=False): bool,
    }
)


def _candidate_hosts(host: str) -> list[str]:
    """Ohne Scheme: https zuerst probieren (Box leitet http auf die
    WebUI-Startseite um, nicht auf dieselbe URL in https)."""
    if host.startswith(("http://", "https://")):
        return [host]
    return ["https://" + host, "http://" + host]


async def _test_connection(hass: HomeAssistant, data: dict[str, str]) -> None:
    """Raise on connection or auth failure. Probiert ggf. beide Schemes."""
    last_err: Exception | None = None
    for host in _candidate_hosts(data[CONF_HOST]):
        client = WlwbxApiClient(
            host,
            data[CONF_USERNAME],
            data[CONF_PASSWORD],
            verify_ssl=data.get(CONF_VERIFY_SSL, True),
        )
        try:
            await client.async_login()
            # Ein lesender Aufruf gegen die Rolle prüfen
            await client.async_get_charging_state()
        except aiohttp.ClientError as err:
            # Mit diesem Scheme nicht erreichbar -> nächstes probieren
            last_err = err
            continue
        except WlwbxApiError:
            # 404 je nach Modell ok – Verbindung steht mit diesem Scheme
            pass
        finally:
            await client.close()
        # Funktionierendes Scheme in die Eingabe zurückschreiben
        data[CONF_HOST] = host
        return
    if last_err is not None:
        raise last_err
    raise WlwbxApiError("Kein Scheme erreichbar")


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
            except WlwbxAuthError:
                errors["base"] = "invalid_auth"
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
