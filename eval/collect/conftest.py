import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from starlette.types import ASGIApp
from dotenv import load_dotenv
from typing import AsyncGenerator

from agents import set_tracing_disabled

from pytest_homeassistant_custom_component.typing import ClientSessionGenerator
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

pytest_plugins = [
    "home_assistant_datasets.plugins.pytest_synthetic_home",
    "home_assistant_datasets.plugins.pytest_scrape",
]

@pytest.fixture(autouse=True, scope="session")
def load_env():
    """Load environment variables from .env files."""
    load_dotenv()

@pytest.fixture(autouse=True)
def disable_tracing():
    set_tracing_disabled(True)

@pytest_asyncio.fixture
async def setup_hass_components(hass: HomeAssistant):
    """Set up the required Home Assistant components for tests."""
    assert await async_setup_component(hass, "http", {"http": {}})
    assert await async_setup_component(hass, "api", {})
    await hass.async_block_till_done()

@pytest_asyncio.fixture
async def addon_app(
    setup_hass_components: None,
    hass_client: ClientSessionGenerator,
    hass_access_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[ASGIApp, None]:
    """
    Fixture that provides a clean, configured instance of the FastAPI app
    for testing.
    """
    # Get HASS connection details
    client = await hass_client()
    host = client.server.host
    port = client.server.port
    base_url = f"http://{host}:{port}"
    ha_api_url = f"{base_url}/api"

    # Set up addon app with proper settings through environment variables
    monkeypatch.setenv("HOME_AGENT_APP_ENV", "test")
    monkeypatch.setenv("HOME_AGENT_HA_API_URL", ha_api_url)
    monkeypatch.setenv("HOME_AGENT_HA_API_KEY", hass_access_token)
    
    from app.main import create_app, get_settings
    
    # Clear the settings cache to ensure the new env vars are loaded
    get_settings.cache_clear()

    async with LifespanManager(create_app()) as manager:
        yield manager.app