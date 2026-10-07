"""Unit tests for STB-Proxy API client and helpers."""

import asyncio
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock

# Mock aiohttp for standalone test
if "aiohttp" not in sys.modules:
    aiohttp_mock = MagicMock()
    class MockClientError(Exception):
        pass
    aiohttp_mock.ClientError = MockClientError
    sys.modules["aiohttp"] = aiohttp_mock

# Load api.py directly by path
api_path = Path(__file__).parent.parent / "custom_components" / "stb_proxy" / "api.py"
spec = importlib.util.spec_from_file_location("api", str(api_path))
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)

STBProxyAuthError = api.STBProxyAuthError
STBProxyClient = api.STBProxyClient
STBProxyConnectionError = api.STBProxyConnectionError
normalize_host = api.normalize_host


class TestNormalizeHost(unittest.TestCase):
    """Test URL normalization function."""

    def test_normalize_without_scheme(self):
        self.assertEqual(normalize_host("localhost:8001"), "http://localhost:8001")
        self.assertEqual(normalize_host("192.168.1.10:8001"), "http://192.168.1.10:8001")

    def test_normalize_with_http_scheme(self):
        self.assertEqual(normalize_host("http://localhost:8001/"), "http://localhost:8001")
        self.assertEqual(normalize_host("http://localhost:8001///"), "http://localhost:8001")

    def test_normalize_with_https_scheme(self):
        self.assertEqual(normalize_host("https://stb.example.com/"), "https://stb.example.com")

    def test_normalize_with_whitespace(self):
        self.assertEqual(normalize_host("  http://10.0.0.5:8001/  "), "http://10.0.0.5:8001")


class TestSTBProxyClient(unittest.IsolatedAsyncioTestCase):
    """Test STBProxyClient methods."""

    def setUp(self):
        self.mock_session = MagicMock()
        self.client = STBProxyClient(
            session=self.mock_session,
            host="http://192.168.1.50:8001",
            api_key="test-api-key-12345",
        )

    def test_properties(self):
        self.assertEqual(self.client.base_url, "http://192.168.1.50:8001")
        self.assertEqual(self.client.host, "http://192.168.1.50:8001")

    def test_headers(self):
        headers = self.client._get_headers()
        self.assertEqual(headers["Authorization"], "Bearer test-api-key-12345")
        self.assertEqual(headers["X-API-Key"], "test-api-key-12345")

    async def test_get_status_success(self):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json = AsyncMock(
            return_value={
                "lineup": 100,
                "streams": 2,
                "blocks": [{"name": "Sports", "enabled": True, "channels": 10, "dead": 0}],
                "plex": {"configured": True, "ok": True, "message": "Synced", "time": "2026-10-07 12:00"},
                "jellyfin": {"configured": False, "ok": False, "message": "", "time": None},
                "otherLogins": 0,
                "boxOn": False,
            }
        )

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        self.mock_session.request.return_value = mock_context

        status = await self.client.async_get_status()
        self.assertEqual(status["lineup"], 100)
        self.assertEqual(status["streams"], 2)
        self.assertEqual(len(status["blocks"]), 1)

    async def test_get_blocks_success(self):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json = AsyncMock(
            return_value=[
                {"name": "Sports", "enabled": True, "channels": 10, "dead": 0},
                {"name": "News", "enabled": False, "channels": 5, "dead": 1},
            ]
        )

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        self.mock_session.request.return_value = mock_context

        blocks = await self.client.async_get_blocks()
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]["name"], "Sports")

    async def test_auth_failure(self):
        mock_response = MagicMock()
        mock_response.status = 401

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        self.mock_session.request.return_value = mock_context

        with self.assertRaises(STBProxyAuthError):
            await self.client.async_get_status()

    async def test_server_error(self):
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        self.mock_session.request.return_value = mock_context

        with self.assertRaises(STBProxyConnectionError):
            await self.client.async_get_status()

    async def test_timeout_error(self):
        self.mock_session.request.side_effect = asyncio.TimeoutError()

        with self.assertRaises(STBProxyConnectionError):
            await self.client.async_get_status()

    async def test_set_block(self):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json = AsyncMock(
            return_value={"name": "Sports Block", "enabled": True, "changed": True}
        )

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        self.mock_session.request.return_value = mock_context

        res = await self.client.async_set_block("Sports Block", True)
        self.assertTrue(res["enabled"])
        self.mock_session.request.assert_called_with(
            method="POST",
            url="http://192.168.1.50:8001/api/blocks/Sports%20Block",
            headers=self.client._get_headers(),
            json={"enabled": True},
        )

    async def test_sync(self):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.json = AsyncMock(
            return_value={"plex": {"ok": True}, "jellyfin": {"ok": False}}
        )

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        self.mock_session.request.return_value = mock_context

        res = await self.client.async_sync()
        self.assertTrue(res["plex"]["ok"])
        self.mock_session.request.assert_called_with(
            method="POST",
            url="http://192.168.1.50:8001/api/sync",
            headers=self.client._get_headers(),
            json=None,
        )


if __name__ == "__main__":
    unittest.main()
