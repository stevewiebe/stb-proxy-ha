"""Button platform for STB-Proxy actions."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import STBProxyDataUpdateCoordinator
from .entity import STBProxyEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up STB-Proxy button entities based on a config entry."""
    coordinator: STBProxyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([STBProxySyncButton(coordinator)])


class STBProxySyncButton(STBProxyEntity, ButtonEntity):
    """Button to trigger media server synchronization in STB-Proxy."""

    def __init__(self, coordinator: STBProxyDataUpdateCoordinator) -> None:
        """Initialize the sync button."""
        super().__init__(coordinator, context="sync_media_servers")
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_sync_media_servers"
        self._attr_name = "Sync Media Servers"
        self._attr_icon = "mdi:sync"

    async def async_press(self) -> None:
        """Handle button press to sync Plex and Jellyfin."""
        _LOGGER.debug("Triggering media server sync via STB-Proxy API")
        await self.coordinator.client.async_sync()
        await self.coordinator.async_request_refresh()
