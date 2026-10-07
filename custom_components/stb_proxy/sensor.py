"""Sensor platform for STB-Proxy."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import STBProxyDataUpdateCoordinator
from .entity import STBProxyEntity


@dataclass(frozen=True, kw_only=True)
class STBProxySensorEntityDescription(SensorEntityDescription):
    """Describes an STB-Proxy sensor entity."""

    value_fn: Callable[[STBProxyDataUpdateCoordinator], Any]
    is_available_fn: Callable[[STBProxyDataUpdateCoordinator], bool] | None = None


SENSOR_DESCRIPTIONS: tuple[STBProxySensorEntityDescription, ...] = (
    STBProxySensorEntityDescription(
        key="active_streams",
        name="Active Streams",
        icon="mdi:play-network",
        native_unit_of_measurement="streams",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: coordinator.streams,
    ),
    STBProxySensorEntityDescription(
        key="available_channels",
        name="Available Channels",
        icon="mdi:television-classic",
        native_unit_of_measurement="channels",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: coordinator.lineup,
    ),
    STBProxySensorEntityDescription(
        key="other_logins",
        name="Other Logins",
        icon="mdi:account-alert",
        native_unit_of_measurement="logins",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda coordinator: coordinator.other_logins,
    ),
    STBProxySensorEntityDescription(
        key="plex_sync_time",
        name="Plex Sync Time",
        icon="mdi:plex",
        value_fn=lambda coordinator: coordinator.plex_status.get("time"),
        is_available_fn=lambda coordinator: bool(
            coordinator.plex_status.get("configured", False)
        ),
    ),
    STBProxySensorEntityDescription(
        key="plex_sync_message",
        name="Plex Sync Status",
        icon="mdi:message-badge-outline",
        value_fn=lambda coordinator: coordinator.plex_status.get("message"),
        is_available_fn=lambda coordinator: bool(
            coordinator.plex_status.get("configured", False)
        ),
    ),
    STBProxySensorEntityDescription(
        key="jellyfin_sync_time",
        name="Jellyfin Sync Time",
        icon="mdi:video-input-antenna",
        value_fn=lambda coordinator: coordinator.jellyfin_status.get("time"),
        is_available_fn=lambda coordinator: bool(
            coordinator.jellyfin_status.get("configured", False)
        ),
    ),
    STBProxySensorEntityDescription(
        key="jellyfin_sync_message",
        name="Jellyfin Sync Status",
        icon="mdi:message-badge-outline",
        value_fn=lambda coordinator: coordinator.jellyfin_status.get("message"),
        is_available_fn=lambda coordinator: bool(
            coordinator.jellyfin_status.get("configured", False)
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up STB-Proxy sensor entities based on a config entry."""
    coordinator: STBProxyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        STBProxySensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class STBProxySensor(STBProxyEntity, SensorEntity):
    """Representation of an STB-Proxy sensor."""

    entity_description: STBProxySensorEntityDescription

    def __init__(
        self,
        coordinator: STBProxyDataUpdateCoordinator,
        description: STBProxySensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, context=description.key)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available:
            return False
        if self.entity_description.is_available_fn is not None:
            return self.entity_description.is_available_fn(self.coordinator)
        return True
