"""Bounded seven-role analysis, durable messages, no registry or execution authority.

Results are committed in the leased job document. Reconciliation derives the
next message from persisted predecessors, so no cross-collection transaction
or exactly-once delivery claim is required. API materializes a proposal only.
"""
import asyncio
import os
import random
import time
from fastapi import HTTPException
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError
from ..models.distributed_schemas import LaunchIn, RoleMessage, RoleResult, ROLES
from . import jobs, knowledge

LEASE_SECONDS = 45
HANDLER_TIMEOUT = 30


def message_id(run_id, role):
    return jobs.digest([run_id, role])


def job_id(run_id, role):
    return jobs.digest([run_id, 'role_work', role])


async def submit(db, business, payload: LaunchIn):
    jobs.persistent(db)
    missing = set(ROLES[:5]) - set(business.enabled_agents)
    if missing:
        raise HTTPException(409, 'Enable all five existing departments for this scenario')
    run_id = jobs.digest([business.id, 'distributed_launch_v1', payload.idempotency_key])
    now = time.time()
    doc = {
        '_id': run_id, 'run_id': run_id, 'business_id': business.id,
        'requested_by': business.owner_user_id, 'schema_version': 1,
        'input': payload.model_dump(), 'status': 'running', 'created_ts': now,
        'deadline_ts': now + payload.duration_seconds,
        'synthetic': True, 'mode': 'rule_based', 'currency': 'USD',
        'ticket_id': jobs.digest([run_id, 'synthetic_ticket']),
        'market_opportunity': random.Random(payload.seed).choice([
            'Synthetic interest in a lower-cost product bundle',
            'Synthetic demand for a focused product launch',
            'Synthetic competitor stock shortage opportunity',
        ]),
    }
    try:
        await db['distributed_runs'].insert_one(doc)
    except DuplicateKeyError:
        doc = await db['distributed_runs'].find_one({'_id': run_id})
        if doc['input'] != payload.model_dump():
            raise HTTPException(409, 'Idempotency key already used with different input')
    await reconcile(db, doc)
    return await read(db, business.id, run_id)


async def terminate(db, run, status):
    # CAS status first: any worker result after this point is ignored by run reads.
    await db['distributed_runs'].update_one(
        {'_id': run['run_id'], 'status': 'running'},
        {'$set': {'status': status, 'ended_ts': time.time()}},
    )
    await db['background_jobs'].update_many(
        {'business_id': run['business_id'], 'kind': 'role_work',
         'payload.correlation_id': run['run_id'],
         'status': {'$in': ['queued', 'running', 'retry_scheduled']}},
        {'$set': {'status': 'cancelled', 'lease_token': None, 'updated_ts': time.time()}},
    )


async def reconcile(db, run):
    if run['status'] != 'running':
        return
    if time.time() >= run['deadline_ts']:
        await terminate(db, run, 'timed_out')
        return
    previous = None
    for role in ROLES:
        item = await db['background_jobs'].find_one({'_id': job_id(run['_id'], role)})
        if item and item['status'] in {'failed', 'cancelled', 'dead_letter'}:
            await terminate(db, run, 'blocked')
            return
        if not item:
            message = RoleMessage(event_id=message_id(run['_id'], role),
                correlation_id=run['_id'], role=role, predecessor_id=previous)
            await jobs.enqueue(db, run['business_id'], run['requested_by'],
                'role_work', message.model_dump(), role,
                # Separate run scope retains existing job semantics elsewhere.
                identity_scope=run['_id'])
            return
        if item['status'] != 'succeeded':
            return
        previous = item['job_id']
    await db['distributed_runs'].update_one(
        {'_id': run['_id'], 'status': 'running'},
        {'$set': {'status': 'ready_for_review', 'ended_ts': time.time()}},
    )


async def read(db, business_id, run_id):
    run = await db['distributed_runs'].find_one({'_id': run_id, 'business_id': business_id})
    if not run:
        raise HTTPException(404, 'Distributed scenario not found')
    await reconcile(db, run)
    run = await db['distributed_runs'].find_one({'_id': run_id, 'business_id': business_id})
    rows = await db['background_jobs'].find({'kind': 'role_work', 'business_id': business_id,
        'payload.correlation_id': run_id}).to_list(length=7)
    by_role = {row['payload']['role']: row for row in rows}
    task = await db['tasks'].find_one({'_id': 'distributed-' + run_id, 'business_id': business_id})
    return {
        **{k: v for k, v in run.items() if k not in {'_id', 'requested_by'}},
        'roles': [{
            'role': role, 'job_id': job_id(run_id, role),
            'status': by_role.get(role, {}).get('status', 'waiting'),
            'attempts': by_role.get(role, {}).get('attempts', 0),
            'event_id': message_id(run_id, role),
            'updated_ts': by_role.get(role, {}).get('updated_ts'),
            'result': by_role.get(role, {}).get('result'),
            'error': by_role.get(role, {}).get('error'),
        } for role in ROLES],
        'task_id': task.get('task_id') if task else None,
        'task_status': task.get('status') if task else None,
        'recorded_outcome': task.get('result') if task else None,
        'report': ('Saved synthetic recommendations. Owner approval and recorded execution are separate.'
                   if not task else f"Linked campaign task is {task['status']}; no external publication is authorized."),
    }


async def handle(db, job):
    message = RoleMessage.model_validate(job['payload'])
    run = await db['distributed_runs'].find_one({'_id': message.correlation_id,
        'business_id': job['business_id'], 'requested_by': job['requested_by']})
    if not run or run['status'] != 'running' or time.time() >= run['deadline_ts']:
        raise HTTPException(409, 'Scenario no longer active')
    if message.event_id != message_id(run['_id'], message.role):
        raise HTTPException(422, 'Invalid event identity')
    index = ROLES.index(message.role)
    expected = job_id(run['_id'], ROLES[index-1]) if index else None
    if message.predecessor_id != expected:
        raise HTTPException(422, 'Invalid predecessor')
    previous = None
    if expected:
        previous = await db['background_jobs'].find_one({'_id': expected,
            'business_id': job['business_id'], 'status': 'succeeded'})
        if not previous:
            raise HTTPException(409, 'Predecessor result is not ready')
    business = await db['businesses'].find_one({'business_id': job['business_id'],
        'owner_user_id': job['requested_by']})
    if not business:
        raise HTTPException(403, 'Workspace ownership changed')
    spec = LaunchIn.model_validate(run['input'])
    account = await db['financial_accounts'].find_one({'_id': job['business_id']})
    available = max(0, account['cash_minor'] - account['reserved_minor']) if account else round(business['starting_budget'] * 100)
    budget = min(spec.requested_budget_minor, available // 10)
    common = dict(role=message.role, mode='rule_based', worker_pid=os.getpid(),
        context_version=account['version'] if account else None,
        reasoning='Structured business reads; budget cap is 10% of current unreserved cash. Recommendations grant no execution authority.')
    role = message.role
    if role == 'ceo':
        result = dict(summary='Delegate synthetic launch analysis to Marketing, Finance, HR, Operations, Support and Strategy.',
            artifact=f'Goal: {spec.goal}\nOpportunity: {run["market_opportunity"]}')
    elif role == 'marketing':
        result = dict(summary='Draft campaign content for owner review; no posting or spending.',
            artifact=f'{spec.campaign_name}\nExplore our upcoming product launch. Ask the team for current availability and approved terms.\nSynthetic draft; no product performance, discount or customer claims are asserted.',
            recommended_budget_minor=spec.requested_budget_minor)
    elif role == 'finance':
        result = dict(summary='Budget constrained' if budget < spec.requested_budget_minor else 'Budget within analysis cap',
            recommended_budget_minor=budget,
            artifact=f'Available cash: {available} minor units. Requested: {spec.requested_budget_minor}. Recommended ceiling: {budget}. Reservations and approval are rechecked by the existing executor.')
    elif role == 'hr':
        result = dict(summary='Assess staffing implication without hiring automatically.',
            artifact=f'Current initial headcount reference: {business["starting_headcount"]}. Launch requires an assigned support reviewer; any recruitment needs a separate approved task.')
    elif role == 'operations':
        result = dict(summary='Check resource constraints before launch.',
            artifact=f'Initial resource reference: {business["starting_resources"]}. Confirm fulfillment capacity before approval; this analysis does not reserve or consume resources.')
    elif role == 'support':
        retrieval = await knowledge.search(db, job['business_id'], 'support', spec.ticket, limit=3)
        sources = retrieval['results']
        citations = [{k: c[k] for k in ('document_id', 'chunk_id', 'version', 'title')} | {'quote': c['text'][:500]} for c in sources]
        common['mode'] = 'extractive_fallback' if citations else 'abstention'
        result = dict(summary='Support response draft; human review required. Escalate unresolved questions to the owner.',
            artifact=('Thank you for contacting us. Authorized reference excerpts:\n' + '\n'.join(f'[{c["title"]} v{c["version"]}] {c["quote"]}' for c in citations)) if citations else 'Thank you for your question. I cannot confirm the policy from authorized sources. I have flagged this for owner review; no refund or delivery promise is made.',
            citations=citations)
    else:
        finance = await db['background_jobs'].find_one({'_id': job_id(run['_id'], 'finance'), 'business_id': job['business_id'], 'status': 'succeeded'})
        ceiling = min(budget, finance['result']['recommended_budget_minor'])
        result = dict(summary='Compare a no-launch baseline against a constrained launch.',
            recommended_budget_minor=ceiling,
            artifact=f'Baseline: no new campaign spend or modeled uplift. Launch budget ceiling: {ceiling} minor units. Risks: demand is synthetic, capacity is unverified, and policy questions require owner review. Recommendation: bounded test only after approval; no ROI is predicted by this rule.')
    return RoleResult(**common, **result).model_dump()


async def run_once(db, role, *, lease_seconds=LEASE_SECONDS, timeout=HANDLER_TIMEOUT):
    if role not in ROLES:
        raise ValueError('Unknown worker role')
    jobs.persistent(db)
    job = await jobs.claim(db, role=role, lease_seconds=lease_seconds)
    if not job:
        return None
    lease = {'_id': job['_id'], 'status': 'running', 'lease_token': job['lease_token']}
    try:
        if job['attempts'] > job['max_attempts']:
            raise HTTPException(422, 'Retry budget exhausted')
        result = await asyncio.wait_for(handle(db, job), timeout=timeout)
        update = {'status': 'succeeded', 'result': result, 'error': None}
    except asyncio.CancelledError:
        # Leave the lease recoverable; shutdown does not claim work succeeded.
        raise
    except Exception as exc:
        poison = isinstance(exc, (ValidationError, HTTPException))
        retry = not poison and job['attempts'] < job['max_attempts']
        update = {'status': 'retry_scheduled' if retry else 'dead_letter',
            'run_after': time.time() + min(60, 2 ** job['attempts']),
            'error': 'Role analysis failed or timed out; no business effects were committed.'}
    lease['lease_until'] = {'$gt': time.time()}
    changed = await db['background_jobs'].update_one(lease, {'$set': {**update,
        'updated_ts': time.time(), 'lease_until': 0}})
    if changed.modified_count:
        return jobs.public({**job, **update})
    return None  # Fenced, cancelled or expired; never report an uncommitted success.
