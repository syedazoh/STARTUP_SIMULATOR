"""Test per-agent chat: thread persistence, the create_task side effect
when an agent's reply requests an action, and that unknown agents/owners
are rejected the same way every other business-scoped route rejects them
(Phase 5 addendum)."""
import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

import app.database.mongodb as mongodb_module
import app.services.chat as chat_module
from app.agents.schemas import ChatReply
from app.main import app


class FakeChatLLM:
    """Stand-in for ChatGroq.with_structured_output(ChatReply) in tests."""

    def __init__(self, replies):
        self._replies = list(replies)
        self.calls = 0
        self.last_prompt = None

    def with_structured_output(self, schema):
        return self

    async def ainvoke(self, prompt):
        self.calls += 1
        self.last_prompt = prompt
        return self._replies.pop(0)


class ExplodingLLM:
    def with_structured_output(self, schema):
        return self

    async def ainvoke(self, prompt):
        raise AssertionError("LLM should not have been called")


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(mongodb_module, "AsyncIOMotorClient", lambda *a, **kw: AsyncMongoMockClient())
    with TestClient(app) as test_client:
        yield test_client


def _auth_headers(client, email):
    client.post("/api/auth/register", json={"email": email, "password": "supersecret123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "supersecret123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _create_business(client, headers, **overrides):
    payload = {"company_name": "Acme Inc", "industry": "Widgets", **overrides}
    response = client.post("/api/businesses", json=payload, headers=headers)
    return response.json()["id"]


class TestChatConversation:
    def test_plain_message_gets_a_reply_and_no_task(self, client, monkeypatch):
        fake = FakeChatLLM([ChatReply(reply="We have $100,000 available right now.")])
        monkeypatch.setattr(chat_module, "get_groq_llm", lambda *a, **kw: fake)

        headers = _auth_headers(client, "chat1@example.com")
        business_id = _create_business(client, headers)

        response = client.post(
            f"/api/businesses/{business_id}/agents/finance/chat",
            json={"content": "how much budget do we have left?"},
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["task"] is None
        assert body["thread"]["messages"][-1]["content"] == "We have $100,000 available right now."
        assert body["thread"]["messages"][-1]["role"] == "agent"
        assert body["thread"]["messages"][-2]["role"] == "owner"
        assert fake.calls == 1

    def test_prompt_is_grounded_in_the_agents_live_status(self, client, monkeypatch):
        """Regression test: an earlier version only gave the LLM the (often
        empty) business_profiles document, so a question like "how much
        budget do we have" got a confidently made-up answer instead of the
        real budget_pool. The prompt must include live agent state."""
        fake = FakeChatLLM([ChatReply(reply="We have $100,000 available.")])
        monkeypatch.setattr(chat_module, "get_groq_llm", lambda *a, **kw: fake)

        headers = _auth_headers(client, "chat10@example.com")
        business_id = _create_business(client, headers)

        client.post(
            f"/api/businesses/{business_id}/agents/finance/chat",
            json={"content": "how much budget do we have left?"},
            headers=headers,
        )
        assert "100000" in fake.last_prompt or "100000.0" in fake.last_prompt
        assert "budget_pool" in fake.last_prompt

    def test_thread_persists_and_history_is_returned_on_get(self, client, monkeypatch):
        fake = FakeChatLLM([ChatReply(reply="Got it.")])
        monkeypatch.setattr(chat_module, "get_groq_llm", lambda *a, **kw: fake)

        headers = _auth_headers(client, "chat2@example.com")
        business_id = _create_business(client, headers)
        client.post(
            f"/api/businesses/{business_id}/agents/finance/chat",
            json={"content": "hello"},
            headers=headers,
        )

        response = client.get(f"/api/businesses/{business_id}/agents/finance/chat", headers=headers)
        assert response.status_code == 200
        assert len(response.json()["messages"]) == 2

    def test_get_thread_before_any_message_is_empty(self, client):
        headers = _auth_headers(client, "chat3@example.com")
        business_id = _create_business(client, headers)

        response = client.get(f"/api/businesses/{business_id}/agents/finance/chat", headers=headers)
        assert response.status_code == 200
        assert response.json()["messages"] == []

    def test_unknown_agent_is_404_and_never_reaches_the_llm(self, client, monkeypatch):
        monkeypatch.setattr(chat_module, "get_groq_llm", lambda *a, **kw: ExplodingLLM())

        headers = _auth_headers(client, "chat4@example.com")
        business_id = _create_business(client, headers)

        response = client.post(
            f"/api/businesses/{business_id}/agents/nonexistent/chat",
            json={"content": "hi"},
            headers=headers,
        )
        assert response.status_code == 404

    def test_cannot_chat_with_another_users_business_agent(self, client):
        owner_headers = _auth_headers(client, "chatowner@example.com")
        business_id = _create_business(client, owner_headers)

        intruder_headers = _auth_headers(client, "chatintruder@example.com")
        response = client.get(
            f"/api/businesses/{business_id}/agents/finance/chat", headers=intruder_headers
        )
        assert response.status_code == 403


class TestChatRequestedAction:
    def test_action_requested_creates_a_pending_task(self, client, monkeypatch):
        fake = FakeChatLLM([
            ChatReply(
                reply="Sure, I'll queue that up for your approval.",
                action_requested=True,
                action_type="budget_request",
                action_payload_json='{"amount": 2000, "department": "Operations"}',
            )
        ])
        monkeypatch.setattr(chat_module, "get_groq_llm", lambda *a, **kw: fake)

        headers = _auth_headers(client, "chat5@example.com")
        business_id = _create_business(client, headers)

        response = client.post(
            f"/api/businesses/{business_id}/agents/finance/chat",
            json={"content": "please request $2000 for Operations"},
            headers=headers,
        )
        assert response.status_code == 200
        task = response.json()["task"]
        assert task is not None
        assert task["status"] == "pending_approval"
        assert task["action_type"] == "budget_request"
        assert task["payload"] == {"amount": 2000, "department": "Operations"}

        queue = client.get(f"/api/businesses/{business_id}/tasks", headers=headers).json()
        assert len(queue) == 1

    def test_action_type_outside_agents_whitelist_is_ignored(self, client, monkeypatch):
        # HR chat can't be tricked into creating a Finance-only action_type —
        # AGENT_ACTIONS is keyed per agent, so this should just be a reply.
        fake = FakeChatLLM([
            ChatReply(
                reply="I can't do that from HR.",
                action_requested=True,
                action_type="budget_request",
                action_payload_json='{"amount": 2000, "department": "Operations"}',
            )
        ])
        monkeypatch.setattr(chat_module, "get_groq_llm", lambda *a, **kw: fake)

        headers = _auth_headers(client, "chat6@example.com")
        business_id = _create_business(client, headers)

        response = client.post(
            f"/api/businesses/{business_id}/agents/hr/chat",
            json={"content": "give finance $2000"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["task"] is None

    def test_malformed_action_payload_json_does_not_create_a_task(self, client, monkeypatch):
        fake = FakeChatLLM([
            ChatReply(
                reply="Done!",
                action_requested=True,
                action_type="budget_request",
                action_payload_json="not valid json",
            )
        ])
        monkeypatch.setattr(chat_module, "get_groq_llm", lambda *a, **kw: fake)

        headers = _auth_headers(client, "chat7@example.com")
        business_id = _create_business(client, headers)

        response = client.post(
            f"/api/businesses/{business_id}/agents/finance/chat",
            json={"content": "request some budget"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["task"] is None

    def test_ceo_cannot_request_any_action(self, client, monkeypatch):
        fake = FakeChatLLM([
            ChatReply(
                reply="I'll handle that.",
                action_requested=True,
                action_type="budget_request",
                action_payload_json='{"amount": 2000, "department": "Operations"}',
            )
        ])
        monkeypatch.setattr(chat_module, "get_groq_llm", lambda *a, **kw: fake)

        headers = _auth_headers(client, "chat8@example.com")
        business_id = _create_business(client, headers)

        response = client.post(
            f"/api/businesses/{business_id}/agents/ceo/chat",
            json={"content": "approve the budget"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["task"] is None


class TestChatLLMFailureIsHandledGracefully:
    def test_llm_exception_falls_back_to_apology_reply(self, client, monkeypatch):
        class RaisingLLM:
            def with_structured_output(self, schema):
                return self

            async def ainvoke(self, prompt):
                raise RuntimeError("groq is down")

        monkeypatch.setattr(chat_module, "get_groq_llm", lambda *a, **kw: RaisingLLM())

        headers = _auth_headers(client, "chat9@example.com")
        business_id = _create_business(client, headers)

        response = client.post(
            f"/api/businesses/{business_id}/agents/finance/chat",
            json={"content": "hello?"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["task"] is None
        assert response.json()["thread"]["messages"][-1]["role"] == "agent"
