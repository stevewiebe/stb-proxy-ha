"""Binary sensor platform for STB-Proxy."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import STBProxyDataUpdateCoordinator
from .entity import STBProxyEntity


@dataclass(frozen=True, kw_only=True)
class STBProxyBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes an STB-Proxy binary sensor entity."""

    is_on_fn: Callable[[STBProxyDataUpdateCoordinator], bool]
    is_available_fn: Callable[[STBProxyDataUpdateCoordinator], bool] | None = None


BINARY_SENSOR_DESCRIPTIONS: tuple[STBProxyBinarySensorEntityDescription, ...] = (
    STBProxyBinarySensorEntityDescription(
        key="box_active",
        name="Box Active",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:power-standby",
        is_on_fn=lambda coordinator: coordinator.box_on,
    ),
    STBProxyBinarySensorEntityDescription(
        key="plex_problem",
        name="Plex Problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert-circle-outline",
        is_on_fn=lambda coordinator: not coordinator.plex_status.get("ok", True),
        is_available_fn=lambda coordinator: bool(
            coordinator.plex_status.get("configured", False)
        ),
    ),
    STBProxyBinarySensorEntityDescription(
        key="jellyfin_problem",
        name="Jellyfin Problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert-circle-outline",
        is_on_fn=lambda coordinator: not coordinator.jellyfin_status.get("ok", True),
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
    """Set up STB-Proxy binary sensors based on a config entry."""
    coordinator: STBProxyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        STBProxyBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class STBProxyBinarySensor(STBProxyEntity, BinarySensorEntity):
    """Representation of an STB-Proxy binary sensor."""

    entity_description: STBProxyBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: STBProxyDataUpdateCoordinator,
        description: STBProxyBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, context=description.key)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        """Return True if the binary sensor is on."""
        return self.entity_description.is_on_fn(self.coordinator)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not super().available:
            return False
        if self.entity_description.is_available_fn is not None:
            return self.entity_description.is_available_fn(self.coordinator)
        return True
