"""DataUpdateCoordinator for STB-Proxy."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import STBProxyAuthError, STBProxyClient, STBProxyConnectionError
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class STBProxyDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching STB-Proxy status data from the API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: STBProxyClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.config_entry = entry

        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({client.host})",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest status data from STB-Proxy."""
        try:
            return await self.client.async_get_status()
        except STBProxyAuthError as err:
            raise ConfigEntryAuthFailed(
                f"STB-Proxy authentication failed. Check your API key: {err}"
            ) from err
        except STBProxyConnectionError as err:
            raise UpdateFailed(f"Error communicating with STB-Proxy: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error updating STB-Proxy: {err}") from err

    @property
    def blocks(self) -> list[dict[str, Any]]:
        """Return the current channel blocks."""
        return self.data.get("blocks", [])

    @property
    def lineup(self) -> int:
        """Return the count of available channels in lineup."""
        return self.data.get("lineup", 0)

    @property
    def streams(self) -> int:
        """Return the count of active streams."""
        return self.data.get("streams", 0)

    @property
    def plex_status(self) -> dict[str, Any]:
        """Return Plex sync status."""
        return self.data.get("plex", {})

    @property
    def jellyfin_status(self) -> dict[str, Any]:
        """Return Jellyfin sync status."""
        return self.data.get("jellyfin", {})

    @property
    def box_on(self) -> bool:
        """Return whether any physical STB box is active on the portals."""
        return bool(self.data.get("boxOn", False))

    @property
    def other_logins(self) -> int:
        """Return the count of other active logins on the portals."""
        return self.data.get("otherLogins", 0)
