import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from starlette.types import ASGIApp
from dotenv import load_dotenv
from typing import AsyncGenerator

from agents import set_tracing_disabled

from app.db.base import Base
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

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

@pytest.fixture(scope="session")
def shared_db_engines():
    """Create a single shared in-memory DB for the whole test session."""
    # Named, shared in-memory database for both async and sync engines
    # Use URI mode via query string per SQLAlchemy docs
    db_uri = "file::memory:?cache=shared&uri=true"

    async_engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_uri}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    sync_engine = create_engine(
        f"sqlite:///{db_uri}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables once for the whole session
    from app.db.base import Base
    async def _create_all():
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    import asyncio as _asyncio
    _asyncio.get_event_loop().run_until_complete(_create_all())

    session_factory = async_sessionmaker(
        bind=async_engine, expire_on_commit=False, class_=AsyncSession
    )

    yield async_engine, sync_engine, session_factory

    # Dispose at the end of the session
    _asyncio.get_event_loop().run_until_complete(async_engine.dispose())
    sync_engine.dispose()


@pytest_asyncio.fixture
async def addon_app(
    setup_hass_components: None,
    hass_client: ClientSessionGenerator,
    hass_access_token: str,
    shared_db_engines,
) -> AsyncGenerator[ASGIApp, None]:
    """
    Function-scoped app that shares a session-scoped in-memory DB across tests.
    """
    # Get HASS connection details
    client = await hass_client()
    host = client.server.host
    port = client.server.port
    base_url = f"http://{host}:{port}"
    ha_api_url = f"{base_url}/api"

    # Build Settings directly
    from app.settings import Settings
    settings = Settings(
        app_env="test",
        ha_api_url=ha_api_url,
        ha_api_key=hass_access_token,
    )

    async_engine, sync_engine, session_factory = shared_db_engines

    # Construct app and override DB dependencies to use shared in-memory DB
    from app.main import create_app
    from app.dependencies import get_db as app_get_db, get_sync_db as app_get_sync_db

    app = create_app(settings)

    async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    def get_test_sync_db():
        return sync_engine

    app.dependency_overrides[app_get_db] = get_test_db
    app.dependency_overrides[app_get_sync_db] = get_test_sync_db

    # Seed a default connection for tests if none exists
    from app.services.connection import ConnectionService
    from app.models import ConnectionCreate, ConnectionUpdate

    async with session_factory() as session:
        existing_connections = await ConnectionService.get_connections(session, mask_key=False)
        if not existing_connections:
            created = await ConnectionService.create_connection(
                session,
                ConnectionCreate(
                    url="http://localhost:8080/v1",
                    api_key="",
                    backend="vllm",
                ),
            )
            await ConnectionService.update_connection(
                session,
                connection_id=created.id,
                connection_update=ConnectionUpdate(
                    model="Qwen/Qwen3-4B-Instruct-2507",
                ),
            )

    async with LifespanManager(app) as manager:
        yield manager.app