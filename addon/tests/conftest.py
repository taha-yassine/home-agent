import pytest
from agents import set_trace_processors
@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture(scope='session', autouse=True)
def remove_default_trace_processor():
    set_trace_processors([])