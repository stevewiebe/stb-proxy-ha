"""Switch platform for STB-Proxy channel blocks."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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
    """Set up STB-Proxy switches from a config entry."""
    coordinator: STBProxyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    tracked_blocks: set[str] = set()

    @callback
    def _check_blocks() -> None:
        """Check for newly added channel blocks and add entities for them."""
        new_entities: list[STBProxyBlockSwitch] = []
        for block in coordinator.blocks:
            block_name = block.get("name")
            if not block_name or block_name in tracked_blocks:
                continue
            tracked_blocks.add(block_name)
            new_entities.append(STBProxyBlockSwitch(coordinator, block_name))

        if new_entities:
            _LOGGER.debug("Adding %d new STB-Proxy block switches", len(new_entities))
            async_add_entities(new_entities)

    # Initial check and add
    _check_blocks()

    # Listen for coordinator updates to dynamically pick up new blocks
    entry.async_on_unload(coordinator.async_add_listener(_check_blocks))


class STBProxyBlockSwitch(STBProxyEntity, SwitchEntity):
    """Switch representation of an STB-Proxy channel block."""

    def __init__(
        self,
        coordinator: STBProxyDataUpdateCoordinator,
        block_name: str,
    ) -> None:
        """Initialize the block switch."""
        super().__init__(coordinator, context=block_name)
        self._block_name = block_name
        slug = block_name.lower().replace(" ", "_")
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_block_{slug}"
        self._attr_name = f"Block {block_name}"
        self._attr_icon = "mdi:television-box"

    def _get_block_data(self) -> dict[str, Any] | None:
        """Find the block dictionary for this switch."""
        for block in self.coordinator.blocks:
            if block.get("name") == self._block_name:
                return block
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available and block exists."""
        return super().available and self._get_block_data() is not None

    @property
    def is_on(self) -> bool:
        """Return True if the block is enabled."""
        block_data = self._get_block_data()
        if block_data:
            return bool(block_data.get("enabled", False))
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes for the block."""
        block_data = self._get_block_data() or {}
        return {
            "block_name": self._block_name,
            "channels": block_data.get("channels", 0),
            "dead_channels": block_data.get("dead", 0),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the channel block."""
        await self.coordinator.client.async_set_block(self._block_name, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the channel block."""
        await self.coordinator.client.async_set_block(self._block_name, False)
        await self.coordinator.async_request_refresh()
