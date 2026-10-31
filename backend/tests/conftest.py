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


@pytest.fixture(autouse=True)
def offline_llm(monkeypatch):
    """Exercise deterministic fallbacks unless a test installs its own model fake."""
    class UnavailableModel:
        def with_structured_output(self, schema):
            if schema.__name__ == "TaskAuthorization":
                class Approval:
                    async def ainvoke(self, prompt):
                        return schema(decision="approve", reason="Explicit test CEO authorization")
                return Approval()
            return self

        async def ainvoke(self, prompt):
            raise RuntimeError("External LLM calls are disabled in tests")

    monkeypatch.setattr("app.core.llm._cached_groq_llm", lambda *args: UnavailableModel())
