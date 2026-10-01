"""CORS configuration test: settings.allowed_origins is what actually
governs the app's CORSMiddleware (main.py), and an origin outside that list
doesn't get Access-Control-Allow-Origin echoed back."""
import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

import app.database.mongodb as mongodb_module
from app.config import settings
from app.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(mongodb_module, "AsyncIOMotorClient", lambda *a, **kw: AsyncMongoMockClient())
    with TestClient(app) as test_client:
        yield test_client


def test_configured_origin_is_echoed_back(client):
    assert settings.allowed_origins, "settings.allowed_origins must be non-empty for this test to mean anything"
    allowed_origin = settings.allowed_origins[0]

    response = client.get("/health", headers={"Origin": allowed_origin})
    assert response.headers.get("access-control-allow-origin") == allowed_origin


def test_disallowed_origin_is_not_echoed_back(client):
    response = client.get("/health", headers={"Origin": "http://evil.example.com"})
    assert "access-control-allow-origin" not in {k.lower() for k in response.headers.keys()}
