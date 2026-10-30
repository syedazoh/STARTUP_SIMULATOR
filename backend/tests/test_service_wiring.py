"""Environment parsing, health routing, and optional provider configuration."""
import asyncio
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

from app.config import Settings
from app.main import app


@pytest.mark.parametrize('value', [
    'http://localhost:5173,http://localhost:8000',
    '["http://localhost:5173", "http://localhost:8000"]',
])
def test_origins_from_real_environment_are_supported(monkeypatch, value):
    monkeypatch.setenv('ALLOWED_ORIGINS', value)
    assert Settings(_env_file=None).allowed_origins == ['http://localhost:5173', 'http://localhost:8000']


def test_dotenv_csv_origins_are_supported(tmp_path):
    env = tmp_path / '.env'
    env.write_text('ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8000\n')
    assert Settings(_env_file=env).allowed_origins == ['http://localhost:5173', 'http://localhost:8000']


def test_proxy_health_route_reports_database_readiness(monkeypatch):
    monkeypatch.setattr('app.database.mongodb.AsyncIOMotorClient', lambda *a, **kw: AsyncMongoMockClient())
    with TestClient(app) as client:
        direct = client.get('/health')
        proxied = client.get('/api/health')
        assert proxied.status_code == 200
        assert direct.json() == proxied.json()
        assert proxied.json()['mongo'] == 'connected'
        assert 'ai_configured' in proxied.json()


def test_missing_groq_key_does_not_crash_model_factory():
    # Run outside the global offline fixture to exercise the real factory.
    import os
    env = {**os.environ, 'GROQ_API_KEY': ''}
    result = subprocess.run([sys.executable, '-c',
        'from app.core.llm import get_groq_llm; assert type(get_groq_llm()).__name__ == "UnconfiguredLLM"'],
        env=env, cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
