"""The STB-Proxy integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import STBProxyClient
from .const import (
    ATTR_BLOCK_NAME,
    ATTR_ENABLED,
    CONF_API_KEY,
    CONF_HOST,
    DOMAIN,
    SERVICE_SET_BLOCK,
    SERVICE_SYNC,
)
from .coordinator import STBProxyDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]

SERVICE_SET_BLOCK_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_BLOCK_NAME): cv.string,
        vol.Required(ATTR_ENABLED): cv.boolean,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up STB-Proxy from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    client = STBProxyClient(
        session=session,
        host=entry.data[CONF_HOST],
        api_key=entry.data[CONF_API_KEY],
    )

    coordinator = STBProxyDataUpdateCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services once
    if len(hass.data[DOMAIN]) == 1:
        async def handle_sync(call: ServiceCall) -> None:
            """Handle the sync service call."""
            for coordinator_instance in hass.data[DOMAIN].values():
                _LOGGER.info("Triggering media server sync on %s", coordinator_instance.client.host)
                await coordinator_instance.client.async_sync()
                await coordinator_instance.async_request_refresh()

        async def handle_set_block(call: ServiceCall) -> None:
            """Handle the set_block service call."""
            block_name = call.data[ATTR_BLOCK_NAME]
            enabled = call.data[ATTR_ENABLED]
            for coordinator_instance in hass.data[DOMAIN].values():
                _LOGGER.info(
                    "Setting block '%s' to %s on %s",
                    block_name,
                    enabled,
                    coordinator_instance.client.host,
                )
                await coordinator_instance.client.async_set_block(block_name, enabled)
                await coordinator_instance.async_request_refresh()

        hass.services.async_register(DOMAIN, SERVICE_SYNC, handle_sync)
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_BLOCK,
            handle_set_block,
            schema=SERVICE_SET_BLOCK_SCHEMA,
        )

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

        # Unregister services if no entries remain
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_SYNC)
            hass.services.async_remove(DOMAIN, SERVICE_SET_BLOCK)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
