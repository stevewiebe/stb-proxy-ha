"""Base entity class for STB-Proxy."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import STBProxyDataUpdateCoordinator


class STBProxyEntity(CoordinatorEntity[STBProxyDataUpdateCoordinator]):
    """Base class for all STB-Proxy entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: STBProxyDataUpdateCoordinator,
        context: str | None = None,
    ) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator, context=context)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=f"STB-Proxy ({coordinator.client.host})",
            manufacturer="STB-Proxy",
            model="STB-Proxy Server",
            configuration_url=coordinator.client.base_url,
            entry_type=DeviceEntryType.SERVICE,
        )
