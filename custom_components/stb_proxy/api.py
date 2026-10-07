"""API Client for STB-Proxy."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import quote, urlparse

import aiohttp

_LOGGER = logging.getLogger(__name__)


class STBProxyError(Exception):
    """Base exception for STB-Proxy errors."""


class STBProxyConnectionError(STBProxyError):
    """Exception raised when unable to connect to STB-Proxy."""


class STBProxyAuthError(STBProxyError):
    """Exception raised when authentication fails."""


def normalize_host(host: str) -> str:
    """Normalize host string to a standard URL format without trailing slash."""
    host = host.strip()
    if not host.startswith(("http://", "https://")):
        host = f"http://{host}"
    return host.rstrip("/")


class STBProxyClient:
    """Asynchronous client for interacting with the STB-Proxy REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        api_key: str,
        timeout: int = 15,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._base_url = normalize_host(host)
        self._api_key = api_key.strip()
        self._timeout = timeout

    @property
    def base_url(self) -> str:
        """Return the base URL of STB-Proxy."""
        return self._base_url

    @property
    def host(self) -> str:
        """Return the normalized host address."""
        return self._base_url

    def _get_headers(self) -> dict[str, str]:
        """Return headers with authorization for requests."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "X-API-Key": self._api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
    ) -> Any:
        """Make an HTTP request to the STB-Proxy server."""
        url = f"{self._base_url}{path}"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                ) as response:
                    if response.status == 401:
                        error_msg = "Authentication failed (401 Unauthorized): Check API key"
                        _LOGGER.error("%s on %s", error_msg, url)
                        raise STBProxyAuthError(error_msg)

                    if response.status >= 400:
                        text = await response.text()
                        error_msg = f"HTTP {response.status} from {url}: {text}"
                        _LOGGER.error(error_msg)
                        raise STBProxyConnectionError(error_msg)

                    content_type = response.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        return await response.json()
                    return await response.text()

        except asyncio.TimeoutError as err:
            error_msg = f"Timeout connecting to STB-Proxy at {url}"
            _LOGGER.error(error_msg)
            raise STBProxyConnectionError(error_msg) from err
        except STBProxyError:
            raise
        except aiohttp.ClientError as err:
            error_msg = f"Network error connecting to STB-Proxy at {url}: {err}"
            _LOGGER.error(error_msg)
            raise STBProxyConnectionError(error_msg) from err
        except Exception as err:
            error_msg = f"Unexpected error connecting to STB-Proxy at {url}: {err}"
            _LOGGER.exception(error_msg)
            raise STBProxyConnectionError(error_msg) from err

    async def async_get_status(self) -> dict[str, Any]:
        """Fetch the full system status from STB-Proxy."""
        data = await self._request("GET", "/api/status")
        if not isinstance(data, dict):
            raise STBProxyConnectionError(f"Unexpected status response: {data}")
        return data

    async def async_get_blocks(self) -> list[dict[str, Any]]:
        """Fetch all channel blocks from STB-Proxy."""
        data = await self._request("GET", "/api/blocks")
        if not isinstance(data, list):
            raise STBProxyConnectionError(f"Unexpected blocks response: {data}")
        return data

    async def async_set_block(self, name: str, enabled: bool) -> dict[str, Any]:
        """Enable or disable a channel block by name."""
        encoded_name = quote(name, safe="")
        data = await self._request(
            "POST",
            f"/api/blocks/{encoded_name}",
            json_data={"enabled": enabled},
        )
        if not isinstance(data, dict):
            raise STBProxyConnectionError(f"Unexpected set_block response: {data}")
        return data

    async def async_sync(self) -> dict[str, Any]:
        """Trigger media server synchronization (Plex / Jellyfin)."""
        data = await self._request("POST", "/api/sync")
        if not isinstance(data, dict):
            raise STBProxyConnectionError(f"Unexpected sync response: {data}")
        return data
