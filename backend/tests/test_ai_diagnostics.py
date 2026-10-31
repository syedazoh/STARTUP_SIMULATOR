"""Provider failure reasons must be actionable and never expose secrets."""

import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
from app.core.llm_errors import (
    LLMNotConfiguredError,
    classify_llm_error,
    report_llm_failure,
)


class ProviderError(Exception):
    def __init__(self, status, code=None):
        super().__init__("PRIVATE_API_KEY and private prompt text")
        self.status_code = status
        self.body = {"error": {"code": code, "message": "PRIVATE_API_KEY"}}


@pytest.mark.parametrize(
    "error,code",
    [
        (LLMNotConfiguredError(), "not_configured"),
        (ProviderError(401), "authentication"),
        (ProviderError(403), "permission_denied"),
        (ProviderError(404), "model_unavailable"),
        (ProviderError(400, "model_decommissioned"), "model_unavailable"),
        (ProviderError(429), "rate_limit"),
        (ProviderError(503), "provider_error"),
        (TimeoutError(), "connection"),
        (ValueError("PRIVATE_API_KEY"), "invalid_response"),
    ],
)
def test_failures_are_classified_without_leaking_provider_details(error, code, caplog):
    failure = report_llm_failure("test", error)
    assert failure.code == code
    assert "PRIVATE_API_KEY" not in failure.message + caplog.text
    assert code in caplog.text


def test_chat_returns_specific_failure_reason(monkeypatch):
    from fastapi.testclient import TestClient
    from mongomock_motor import AsyncMongoMockClient
    from app.main import app
    import app.services.chat as chat

    class FailedModel:
        def with_structured_output(self, schema):
            return self

        async def ainvoke(self, prompt):
            raise ProviderError(400, "model_decommissioned")

    monkeypatch.setattr(
        "app.database.mongodb.AsyncIOMotorClient",
        lambda *a, **kw: AsyncMongoMockClient(),
    )
    monkeypatch.setattr(chat, "get_groq_llm", lambda: FailedModel())
    with TestClient(app) as client:
        credentials = {"email": "ai-test@example.com", "password": "supersecret123"}
        client.post("/api/auth/register", json=credentials)
        token = client.post("/api/auth/login", json=credentials).json()["access_token"]
        headers = {"Authorization": "Bearer " + token}
        bid = client.post(
            "/api/businesses",
            json={"company_name": "Test", "industry": "Software"},
            headers=headers,
        ).json()["id"]
        response = client.post(
            f"/api/businesses/{bid}/agents/finance/chat",
            json={"content": "What is our budget?"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["ai_error"] == "model_unavailable"
        assert (
            "model is unavailable"
            in response.json()["thread"]["messages"][-1]["content"]
        )
        assert "PRIVATE_API_KEY" not in response.text


def test_summary_retains_deterministic_results_and_reports_reason():
    from app.agents.ceo_agent import CEOAgent

    class FailedModel:
        async def ainvoke(self, prompt):
            raise ProviderError(429)

    ceo = CEOAgent()
    ceo._summary_llm = FailedModel()
    result = asyncio.run(
        ceo.summarize_run(
            [{"tick": 1, "event_type": "budget_request", "data": {"amount": 100}}]
        )
    )
    assert "1 ticks" in result.headline
    assert "request limit" in result.risks[0]
    assert "PRIVATE_API_KEY" not in str(result)


def load_probe():
    path = Path(__file__).resolve().parents[2] / "scripts/check_ai.py"
    spec = importlib.util.spec_from_file_location("probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_diagnostic_command_handles_success_without_printing_key(monkeypatch, capsys):
    probe = load_probe()

    class Model:
        def with_structured_output(self, schema):
            return self

        async def ainvoke(self, prompt):
            return SimpleNamespace(ok=True)

    monkeypatch.setattr(probe.settings, "groq_api_key", "PRIVATE_API_KEY")
    monkeypatch.setattr(probe, "get_groq_llm", lambda: Model())
    assert asyncio.run(probe.check()) == 0
    output = capsys.readouterr().out
    assert "PASSED" in output and "PRIVATE_API_KEY" not in output


def test_diagnostic_command_reports_failed_credentials_safely(monkeypatch, capsys):
    probe = load_probe()

    class Model:
        def with_structured_output(self, schema):
            return self

        async def ainvoke(self, prompt):
            raise ProviderError(401)

    monkeypatch.setattr(probe.settings, "groq_api_key", "PRIVATE_API_KEY")
    monkeypatch.setattr(probe, "get_groq_llm", lambda: Model())
    assert asyncio.run(probe.check()) == 1
    output = capsys.readouterr().out
    assert "[authentication]" in output and "PRIVATE_API_KEY" not in output
