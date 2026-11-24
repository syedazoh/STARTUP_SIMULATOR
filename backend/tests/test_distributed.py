"""No live models/providers. Queue fences, ordering, ownership and safe artifacts."""
import asyncio
import time
from datetime import datetime, timezone
import pytest
from fastapi import HTTPException
from mongomock_motor import AsyncMongoMockClient
from app.models.business_schemas import BusinessOut
from app.models.distributed_schemas import LaunchIn, ROLES
from app.services import distributed as work, jobs
from tests.test_account_isolation import accounts  # noqa: F401


async def setup():
    db = AsyncMongoMockClient().db
    b = BusinessOut(id='a', owner_user_id='owner', company_name='Synthetic', industry='Software',
        starting_budget=1000, starting_customer_base=10, starting_headcount=2,
        starting_resources=30, enabled_agents=list(ROLES[:5]), created_at=datetime.now(timezone.utc))
    await db['businesses'].insert_one({**b.model_dump(), 'business_id': b.id})
    return db, b


@pytest.mark.asyncio
async def test_seven_roles_ordered_idempotent_and_no_business_effects():
    db, b = await setup()
    p = LaunchIn(idempotency_key='same')
    run = await work.submit(db, b, p)
    assert (await work.submit(db, b, p))['run_id'] == run['run_id']
    with pytest.raises(HTTPException):
        await work.submit(db, b, p.model_copy(update={'seed': 42}))
    assert await jobs.claim(db) is None  # API worker must not steal role messages.
    assert await work.run_once(db, 'finance') is None  # Predecessor not done.
    for role in ROLES:
        result = await work.run_once(db, role)
        assert result['status'] == 'succeeded'
        assert result['result']['role'] == role
        run = await work.read(db, b.id, run['run_id'])
    assert run['status'] == 'ready_for_review'
    assert run['roles'][2]['result']['recommended_budget_minor'] == 10000
    assert run['roles'][5]['result']['mode'] == 'abstention'
    assert 'owner review' in run['roles'][5]['result']['artifact']
    assert 'no product performance' in run['roles'][1]['result']['artifact']
    assert await db['financial_accounts'].count_documents({}) == 0
    assert await db['tasks'].count_documents({}) == 0
    with pytest.raises(HTTPException):
        await work.read(db, 'other', run['run_id'])
    assert await db['background_jobs'].count_documents({}) == 7


@pytest.mark.asyncio
async def test_crash_recovery_claim_race_cancel_and_late_fence(monkeypatch):
    db, b = await setup()
    run = await work.submit(db, b, LaunchIn(idempotency_key='crash'))
    claims = await asyncio.gather(*[jobs.claim(db, role='ceo', lease_seconds=.01) for _ in range(2)])
    assert sum(x is not None for x in claims) == 1
    first = next(x for x in claims if x)
    await asyncio.sleep(.02)
    assert (await work.run_once(db, 'ceo'))['attempts'] == 2
    late = await db['background_jobs'].update_one({'_id': first['_id'], 'lease_token': first['lease_token']}, {'$set': {'result': 'stale'}})
    assert late.matched_count == 0
    run = await work.read(db, b.id, run['run_id'])
    async def cancel_during_handle(*args):
        row = await db['distributed_runs'].find_one({'_id': run['run_id']})
        await work.terminate(db, row, 'cancelled')
        return {'forged': True}
    monkeypatch.setattr(work, 'handle', cancel_during_handle)
    assert await work.run_once(db, 'marketing') is None
    assert (await work.read(db, b.id, run['run_id']))['status'] == 'cancelled'
    item = await db['background_jobs'].find_one({'_id': work.job_id(run['run_id'], 'marketing')})
    assert item['result'] is None and item['status'] == 'cancelled'


@pytest.mark.asyncio
async def test_timeout_poison_and_bounded_retry(monkeypatch):
    db, b = await setup()
    run = await work.submit(db, b, LaunchIn(idempotency_key='retry'))
    async def slow(*args):
        await asyncio.sleep(1)
    monkeypatch.setattr(work, 'handle', slow)
    for attempt in range(3):
        await db['background_jobs'].update_one({'_id': work.job_id(run['run_id'], 'ceo')}, {'$set': {'run_after': 0}})
        result = await work.run_once(db, 'ceo', timeout=.001)
    assert result['status'] == 'dead_letter' and result['attempts'] == 3
    assert (await work.read(db, b.id, run['run_id']))['status'] == 'blocked'
    run = await work.submit(db, b, LaunchIn(idempotency_key='poison'))
    await db['background_jobs'].update_one({'_id': work.job_id(run['run_id'], 'ceo')}, {'$set': {'payload.schema_version': 99}})
    monkeypatch.undo()
    assert (await work.run_once(db, 'ceo'))['status'] == 'dead_letter'
    run = await work.submit(db, b, LaunchIn(idempotency_key='deadline'))
    await db['distributed_runs'].update_one({'_id': run['run_id']}, {'$set': {'deadline_ts': 0}})
    assert (await work.read(db, b.id, run['run_id']))['status'] == 'timed_out'


@pytest.mark.asyncio
async def test_support_only_reads_authorized_fresh_documents(monkeypatch):
    from app.config import settings
    from app.models.automation_schemas import DocumentIn
    from app.services import knowledge
    monkeypatch.setattr(settings, 'background_jobs_enabled', True)
    monkeypatch.setattr(settings, 'rag_dense_enabled', False)
    monkeypatch.setattr(settings, 'rag_reranker_enabled', False)
    db, b = await setup()
    for key, roles, text in [('public', ['support'], 'Launch return policy: ask the owner to review any return.'),
                            ('private', ['finance'], 'Secret return policy for finance only.')]:
        doc = await knowledge.submit_document(db, b, b.owner_user_id,
            DocumentIn(key=key, title=key, departments=roles, text=text))
        await knowledge.index_document(db, b.id, doc['payload']['document_id'], doc['payload']['version'])
    run = await work.submit(db, b, LaunchIn(idempotency_key='citations'))
    for role in ROLES[:6]:
        done = await work.run_once(db, role)
        await work.read(db, b.id, run['run_id'])
    result = done['result']
    assert result['mode'] == 'extractive_fallback'
    assert len(result['citations']) == 1
    assert result['citations'][0]['title'] == 'public'
    assert 'Secret' not in result['artifact']


def test_api_tenants_contracts_and_existing_approval_authority(accounts):
    c, h, a, b = accounts
    root = f'/api/businesses/{a}/distributed-runs'
    assert c.post(root, headers=h['bob'], json={'idempotency_key': 'x'}).status_code == 403
    assert c.post(root, headers=h['alice'], json={'idempotency_key': 'x', 'business_id': b}).status_code == 422
    run = c.post(root, headers=h['alice'], json={'idempotency_key': 'x'}).json()
    assert c.post(root+'/'+run['run_id']+'/proposal', headers=h['alice']).status_code == 409
    for role in ROLES:
        asyncio.run(work.run_once(c.app.state.db, role))
        c.get(root+'/'+run['run_id'], headers=h['alice'])
    result = c.post(root+'/'+run['run_id']+'/proposal', headers=h['alice'])
    assert result.status_code == 201, result.text
    task = result.json()
    assert task['status'] == 'pending_approval' and task['result'] is None
    assert c.get(f'/api/businesses/{b}/distributed-runs/'+run['run_id'], headers=h['bob']).status_code == 404
    repeated = c.post(root+'/'+run['run_id']+'/proposal', headers=h['alice']).json()
    assert repeated['id'] == task['id']
    assert c.post('/api/tasks/'+task['id']+'/approve', headers=h['bob']).status_code == 403
    approved = c.post('/api/tasks/'+task['id']+'/approve', headers=h['alice'], json={'expected_fingerprint': task['approval_fingerprint']})
    assert approved.status_code == 200 and approved.json()['status'] == 'executed'
    report = c.get(root+'/'+run['run_id'], headers=h['alice']).json()
    assert report['task_status'] == 'executed' and report['recorded_outcome']

@pytest.mark.asyncio
async def test_completed_before_deadline_survives_delayed_reconciliation():
    db, b = await setup()
    run = await work.submit(db, b, LaunchIn(idempotency_key='delayed-summary'))
    for role in ROLES:
        await work.run_once(db, role)
        if role != ROLES[-1]:
            await work.read(db, b.id, run['run_id'])
    last = await db['background_jobs'].find_one({'_id': work.job_id(run['run_id'], 'strategy')})
    await db['distributed_runs'].update_one({'_id':run['run_id']}, {'$set': {'deadline_ts':last['updated_ts']+.005}})
    await asyncio.sleep(.01)
    assert (await work.read(db,b.id,run['run_id']))['status']=='ready_for_review'


@pytest.mark.asyncio
async def test_current_recorded_staffing_resources_and_predecessor_budget():
    db, b = await setup()
    for role,state in [('hr',{'employee_count':9}),('operations',{'resource_pool':70})]:
        await db['agent_snapshots'].insert_one({'business_id':b.id,'agent_id':role+'_'+b.id,
            'state':state,'timestamp':datetime.now(timezone.utc)})
        await db['agent_snapshots'].insert_one({'business_id':'other','agent_id':role+'_'+b.id,
            'state':{'employee_count':999,'resource_pool':999},'timestamp':datetime.now(timezone.utc)})
    run=await work.submit(db,b,LaunchIn(idempotency_key='current-state'))
    for role in ROLES:
        await work.run_once(db,role)
        run=await work.read(db,b.id,run['run_id'])
    assert 'Latest recorded headcount: 9' in run['roles'][3]['result']['artifact']
    assert 'Latest recorded resource pool: 70' in run['roles'][4]['result']['artifact']
    assert 'Finance ceiling: 10000' in run['roles'][3]['result']['artifact']
    assert 'Latest recorded headcount: 999' not in run['roles'][3]['result']['artifact']
    assert 'Latest recorded resource pool: 999' not in run['roles'][4]['result']['artifact']

@pytest.mark.asyncio
async def test_result_completing_after_deadline_is_not_success(monkeypatch):
    db,b=await setup()
    run=await work.submit(db,b,LaunchIn(idempotency_key='late-result'))
    handler=work.handle
    async def expired(db,job):
        result=await handler(db,job)
        await db['distributed_runs'].update_one({'_id':run['run_id']},{'$set':{'deadline_ts':0}})
        return result
    monkeypatch.setattr(work,'handle',expired)
    assert (await work.run_once(db,'ceo'))['status']=='dead_letter'
    assert (await work.read(db,b.id,run['run_id']))['status']=='timed_out'
