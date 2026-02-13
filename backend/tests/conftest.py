import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _init_app():
    """Use TestClient as a context manager so startup/shutdown events fire."""
    with TestClient(app):
        yield


@pytest.fixture()
def client():
    """Provide a TestClient that shares the already-initialized app."""
    return TestClient(app, raise_server_exceptions=True)
