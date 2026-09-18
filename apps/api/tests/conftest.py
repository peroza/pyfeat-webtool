import pytest
from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@contextmanager
def api_test_client():
    """TestClient context manager so FastAPI lifespan runs (store/runner on app.state)."""
    with TestClient(create_app()) as client:
        yield client
