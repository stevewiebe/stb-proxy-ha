"""Config flow for STB-Proxy integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    STBProxyAuthError,
    STBProxyClient,
    STBProxyConnectionError,
    normalize_host,
)
from .const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    DEFAULT_HOST,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_API_KEY): str,
    }
)


class STBProxyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for STB-Proxy."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step where the user enters host and api_key."""
        errors: dict[str, str] = {}

        if user_input is not None:
            normalized_host = normalize_host(user_input[CONF_HOST])
            api_key = user_input[CONF_API_KEY].strip()

            session = async_get_clientsession(self.hass)
            client = STBProxyClient(session=session, host=normalized_host, api_key=api_key)

            try:
                await client.async_get_status()
            except STBProxyAuthError:
                errors["base"] = "invalid_auth"
            except STBProxyConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during STB-Proxy config validation")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(normalized_host)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"STB-Proxy ({normalized_host})",
                    data={
                        CONF_HOST: normalized_host,
                        CONF_API_KEY: api_key,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return STBProxyOptionsFlow(config_entry)


class STBProxyOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for STB-Proxy."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self._config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current_interval,
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
                }
            ),
        )
