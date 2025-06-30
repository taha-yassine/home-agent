"""Constants for the Home Agent integration."""

DOMAIN = "home_agent"

# Configuration
ADDON_URL = "http://localhost:8000"  # TODO: change to the actual addon url; see https://developers.home-assistant.io/docs/add-ons/communication#network

# Conversation settings
DEFAULT_MAX_HISTORY = 10  # Number of messages to keep in history
MAX_HISTORY_SECONDS = 600  # How long to keep conversation history (10 minutes)
