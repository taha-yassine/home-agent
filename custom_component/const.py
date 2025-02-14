"""Constants for the Home Agent integration."""

DOMAIN = "home_agent"
CONF_SERVER_URL = "server_url"

# Configuration
CONF_ADDON_URL = "addon_url"
DEFAULT_ADDON_URL = "http://localhost:8000"

# Conversation settings
DEFAULT_MAX_HISTORY = 10  # Number of messages to keep in history
MAX_HISTORY_SECONDS = 600  # How long to keep conversation history (10 minutes)
