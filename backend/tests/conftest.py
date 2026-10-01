"""Global pytest fixtures for backend tests"""
import pytest
from cryptography.fernet import Fernet

from app.config import settings
from app.core.crypto import _master_fernet

_TEST_FERNET_KEY = Fernet.generate_key().decode()


@pytest.fixture(autouse=True)
def setup_test_master_key(monkeypatch):
    """Ensure tests run with a valid, generated test credential master key
    rather than the published default master key."""
    monkeypatch.setattr(settings, "credential_master_key", _TEST_FERNET_KEY)
    _master_fernet.cache_clear()
    yield
    _master_fernet.cache_clear()
