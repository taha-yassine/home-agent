"""Constants for the Home Agent integration."""

DOMAIN = "home_agent"

# Generated using hashlib.sha1("https://github.com/taha-yassine/home-agent".lower().encode()).hexdigest()[:8]
# See https://developers.home-assistant.io/docs/add-ons/communication#network
# TODO: Avoid hardcoding/make it configurable
# TODO: Potentially implement discovery
ADDON_URL = "9bd46c1b-home-agent"

DEFAULT_MAX_HISTORY = 10  # Number of messages to keep in history
MAX_HISTORY_SECONDS = 600  # How long to keep conversation history (10 minutes)

CONF_STREAMING = "streaming"
DEFAULT_STREAMING = True
