"""Regressions for local decision logs and bounded structured AI requests."""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import BaseModel

from app.core import llm, llm_runtime
from app.core.llm_errors import LLMCallFailed, classify_llm_error, report_llm_failure
from app.database.mongodb import InMemoryDatabase

REAL_FACTORY = llm._cached_groq_llm


class ProviderError(Exception):
    def __init__(self, status=429, delay=None, code=None, param=None):
        super().__init__('PRIVATE_KEY PRIVATE_PROMPT')
        self.status_code = status
        self.body = {'error': {'code': code, 'param': param, 'message': 'PRIVATE_KEY'}}
        self.response = SimpleNamespace(headers={} if delay is None else {'retry-after': delay})


class Clock:
    now = 0.0

    def time(self):
        return self.now

    async def sleep(self, delay):
        self.now += delay
        await asyncio.sleep(0)


@pytest.mark.asyncio
@pytest.mark.parametrize('direction,expected', [(1, ['missing', 'null', 'one', 'two']), (-1, ['two', 'one', 'missing', 'null'])])
async def test_memory_sort_preserves_manual_and_simulation_records(direction, expected):
    db = InMemoryDatabase()
    for doc in [{'name': 'two', 'tick': 2}, {'name': 'missing'}, {'name': 'null', 'tick': None}, {'name': 'one', 'tick': 1}]:
        await db['decisions'].insert_one(doc)
    docs = await db['decisions'].find({}).sort('tick', direction).to_list(100)
    assert [doc['name'] for doc in docs] == expected
    assert await db['decisions'].count_documents({}) == 4


def test_local_decision_log_and_run_history_http(monkeypatch):
    from fastapi.testclient import TestClient
    from mongomock_motor import AsyncMongoMockClient
    from app.main import app
    from app.config import settings

    monkeypatch.setattr('app.database.mongodb.AsyncIOMotorClient', lambda *a, **k: AsyncMongoMockClient())
    monkeypatch.setattr(settings, 'allow_in_memory_login', True)
    with TestClient(app) as client:
        app.state.db = InMemoryDatabase()
        credentials = {'email': 'history@example.com', 'password': 'supersecret123'}
        assert client.post('/api/auth/register', json=credentials).status_code == 201
        token = client.post('/api/auth/login', json=credentials).json()['access_token']
        headers = {'Authorization': 'Bearer ' + token}
        bid = client.post('/api/businesses', json={'company_name': 'History', 'industry': 'Software'}, headers=headers).json()['id']
        async def seed():
            for extra in [{'tick': 2}, {'tick': None}, {}, {'tick': 1}]:
                await app.state.db['decision_logs'].insert_one({'business_id': bid, 'event_type': 'budget_request', **extra})
            await app.state.db['simulation_runs'].insert_one({'business_id': bid, 'run_id': 'test-run', 'started_at': '2026-01-01'})
        client.portal.call(seed)
        response = client.get(f'/api/businesses/{bid}/simulation/decision-log', headers=headers)
        assert response.status_code == 200
        assert [doc.get('tick') for doc in response.json()] == [None, None, 1, 2]
        history = client.get(f'/api/businesses/{bid}/simulation/simulation-runs', headers=headers)
        assert history.status_code == 200
        assert history.json()[0]['run_id'] == 'test-run'


@pytest.mark.asyncio
async def test_retry_after_is_respected_and_attempt_budget_is_bounded():
    clock = Clock()
    gate = llm_runtime.RequestGate(0, clock=clock.time, sleep=clock.sleep)
    calls = []
    async def call():
        calls.append(clock.now)
        if len(calls) == 1:
            raise ProviderError(delay='7')
        return 'ok'
    assert await gate.invoke(call) == 'ok'
    assert calls == [0, 7]
    failure = AsyncMock(side_effect=ProviderError(delay='0'))
    with pytest.raises(LLMCallFailed):
        await gate.invoke(failure)
    assert failure.await_count == 2


@pytest.mark.asyncio
async def test_long_cooldown_survives_failure_and_blocks_other_requests():
    clock = Clock()
    gate = llm_runtime.RequestGate(0, clock=clock.time, sleep=clock.sleep)
    call = AsyncMock(side_effect=ProviderError(delay='120'))
    for _ in range(2):
        with pytest.raises(LLMCallFailed) as exc:
            await gate.invoke(call)
        assert classify_llm_error(exc.value).code == 'rate_limit'
    assert call.await_count == 1
    assert gate.next_start == 120


@pytest.mark.asyncio
async def test_requests_are_serialized_and_spaced():
    clock = Clock()
    gate = llm_runtime.RequestGate(2, clock=clock.time, sleep=clock.sleep)
    active, maximum, starts = 0, 0, []
    async def call():
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        starts.append(clock.now)
        await asyncio.sleep(0)
        active -= 1
        return 'ok'
    assert await asyncio.gather(*(gate.invoke(call) for _ in range(4))) == ['ok'] * 4
    assert maximum == 1
    assert starts == [0, 2, 4, 6]


@pytest.mark.asyncio
async def test_queue_limit_cancellation_and_timeout_release_gate(monkeypatch):
    monkeypatch.setattr(llm_runtime, 'MAX_PENDING_REQUESTS', 1)
    gate = llm_runtime.RequestGate(0)
    entered, release = asyncio.Event(), asyncio.Event()
    async def block():
        entered.set()
        await release.wait()
    task = asyncio.create_task(gate.invoke(block))
    await entered.wait()
    with pytest.raises(LLMCallFailed):
        await gate.invoke(AsyncMock())
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert gate.pending == 0
    monkeypatch.setattr(llm_runtime, 'TOTAL_TIMEOUT_SECONDS', 0.02)
    with pytest.raises(LLMCallFailed) as exc:
        await gate.invoke(block)
    assert classify_llm_error(exc.value).code == 'connection'
    assert await gate.invoke(AsyncMock(return_value='recovered')) == 'recovered'


@pytest.mark.asyncio
@pytest.mark.parametrize('status', [400, 401, 403, 404])
async def test_permanent_provider_errors_are_not_retried(status):
    call = AsyncMock(side_effect=ProviderError(status))
    with pytest.raises(LLMCallFailed):
        await llm_runtime.RequestGate(0).invoke(call)
    assert call.await_count == 1


@pytest.mark.parametrize('code,param,expected', [
    ('tool_use_failed', 'tools', 'structured_output'),
    ('context_length_exceeded', 'messages', 'context_length'),
    ('unsupported_parameter', 'response_format', 'invalid_request'),
    ('PRIVATE_KEY', 'PRIVATE_PROMPT', 'invalid_request'),
])
def test_400_diagnostics_are_specific_and_allowlisted(code, param, expected, caplog):
    error = ProviderError(400, code=code, param=param)
    failure = report_llm_failure('chat', LLMCallFailed(error))
    assert failure.code == expected
    assert 'PRIVATE_KEY' not in caplog.text + failure.message
    assert 'PRIVATE_PROMPT' not in caplog.text + failure.message
    if code != 'PRIVATE_KEY':
        assert code in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize('payload,valid', [({'ok': True}, True), ({'ok': 'not a boolean'}, False)])
async def test_real_groq_adapter_uses_json_mode_and_validates_locally(payload, valid):
    from langchain_groq import ChatGroq
    class Reply(BaseModel):
        ok: bool
    requests = []
    async def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={
            'id': 'test', 'object': 'chat.completion', 'created': 1, 'model': 'openai/gpt-oss-120b',
            'choices': [{'index': 0, 'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': json.dumps(payload)}}],
        })
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle), trust_env=False) as http_client:
        raw = ChatGroq(groq_api_key='test-not-a-real-key', model='openai/gpt-oss-120b', max_retries=0, client=SimpleNamespace(), http_async_client=http_client)
        response = llm.ManagedLLM(raw).with_structured_output(Reply)
        if valid:
            assert (await response.ainvoke('Please respond.')).ok is True
        else:
            with pytest.raises(LLMCallFailed):
                await response.ainvoke('Please respond.')
    assert len(requests) == 1
    assert requests[0]['response_format'] == {'type': 'json_object'}
    assert 'tools' not in requests[0]
    assert '"ok"' in requests[0]['messages'][0]['content']


def test_real_factory_disables_hidden_sdk_retries(monkeypatch):
    kwargs = {}
    def create(**values):
        kwargs.update(values)
        return SimpleNamespace()
    monkeypatch.setattr(llm, 'ChatGroq', create)
    monkeypatch.setattr(llm.settings, 'groq_api_key', 'test-not-a-real-key')
    REAL_FACTORY.cache_clear()
    try:
        REAL_FACTORY(0)
        assert kwargs['max_retries'] == 0
        assert kwargs['timeout'] == 20
    finally:
        REAL_FACTORY.cache_clear()


@pytest.mark.asyncio
@pytest.mark.parametrize('name,event', [
    ('finance', {'type': 'budget_request', 'amount': 10, 'department': 'Operations'}),
    ('marketing', {'type': 'campaign_launch', 'campaign_name': 'Test', 'requested_budget': 10}),
    ('hr', {'type': 'recruitment_request', 'role': 'Engineer', 'headcount': 1}),
    ('operations', {'type': 'resource_request', 'resource_type': 'Compute', 'quantity': 1}),
])
async def test_agent_graph_does_not_multiply_managed_retries(name, event, monkeypatch):
    import importlib
    module = importlib.import_module(f'app.agents.{name}_agent')
    memory = SimpleNamespace(query_similar=lambda *a, **k: [], add_decision=lambda **k: None)
    monkeypatch.setattr(module, 'get_decision_memory_store', lambda: memory)
    cls = {'finance': 'FinanceAgent', 'marketing': 'MarketingAgent', 'hr': 'HRAgent', 'operations': 'OperationsAgent'}[name]
    agent = getattr(module, cls)()
    agent._structured_llm = AsyncMock()
    agent._structured_llm.ainvoke.side_effect = LLMCallFailed(ProviderError())
    await agent.process_event(event)
    assert agent._structured_llm.ainvoke.await_count == 1


@pytest.mark.parametrize('provider_code,expected', [('tool_use_failed', 'structured_output'), ('unsupported_parameter', 'invalid_request')])
def test_rejected_chat_is_visible_and_never_creates_a_task(monkeypatch, provider_code, expected):
    from fastapi.testclient import TestClient
    from mongomock_motor import AsyncMongoMockClient
    from app.main import app
    import app.services.chat as chat

    class Rejected:
        def with_structured_output(self, schema):
            return self
        async def ainvoke(self, prompt):
            raise ProviderError(400, code=provider_code, param='response_format')

    monkeypatch.setattr('app.database.mongodb.AsyncIOMotorClient', lambda *a, **k: AsyncMongoMockClient())
    monkeypatch.setattr(chat, 'get_groq_llm', lambda: Rejected())
    with TestClient(app) as client:
        credentials = {'email': 'rejected@example.com', 'password': 'supersecret123'}
        client.post('/api/auth/register', json=credentials)
        token = client.post('/api/auth/login', json=credentials).json()['access_token']
        headers = {'Authorization': 'Bearer ' + token}
        bid = client.post('/api/businesses', json={'company_name': 'Rejected', 'industry': 'Software'}, headers=headers).json()['id']
        reply = client.post(f'/api/businesses/{bid}/agents/marketing/chat', json={'content': 'Launch a campaign'}, headers=headers)
        assert reply.status_code == 200
        assert reply.json()['ai_error'] == expected
        assert reply.json()['task'] is None
        assert client.get(f'/api/businesses/{bid}/tasks', headers=headers).json() == []
        assert 'PRIVATE_KEY' not in reply.text


@pytest.mark.asyncio
async def test_unavailable_ceo_review_is_marked_honestly(monkeypatch):
    from app.agents.ceo_agent import CEOAgent
    class Rejected:
        def with_structured_output(self, schema):
            return self
        async def ainvoke(self, prompt):
            raise ProviderError(delay='60')
    monkeypatch.setattr('app.agents.ceo_agent.get_groq_llm', lambda: Rejected())
    review = await CEOAgent().review_department_report({'status': 'denied', 'success_criteria': 'Grow customers'})
    assert review['ai_error'] == 'rate_limit'
    assert review['next_action'] == 'owner_attention'
    assert '60 seconds' in review['assessment']
