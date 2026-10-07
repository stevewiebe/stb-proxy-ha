"""Constants for the STB-Proxy integration."""

DOMAIN = "stb_proxy"

# Configuration and options keys
CONF_HOST = "host"
CONF_API_KEY = "api_key"
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_NAME = "STB-Proxy"
DEFAULT_HOST = "http://localhost:8001"
DEFAULT_SCAN_INTERVAL = 30  # seconds

# Services
SERVICE_SYNC = "sync"
SERVICE_SET_BLOCK = "set_block"

# Service Attributes
ATTR_BLOCK_NAME = "block_name"
ATTR_ENABLED = "enabled"
