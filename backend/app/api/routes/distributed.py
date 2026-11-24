"""Owner-controlled synthetic launch analysis. Workers cannot approve or execute."""
from fastapi import APIRouter, Depends, HTTPException, Request
from ..deps import get_owned_business
from ...models.distributed_schemas import LaunchIn
from ...models.task_schemas import to_task_out
from ...core.rate_limit import RateLimiter, rate_limit_dependency
from ...services import distributed
from ...services.tasks import create_task

router = APIRouter(prefix='/api/businesses/{business_id}/distributed-runs',
    tags=['distributed simulation'],
    dependencies=[Depends(rate_limit_dependency(RateLimiter(max_requests=90, window_seconds=60)))])


@router.post('', status_code=202)
async def submit(payload: LaunchIn, request: Request, business=Depends(get_owned_business)):
    return await distributed.submit(request.app.state.db, business, payload)


@router.get('')
async def listing(request: Request, business=Depends(get_owned_business)):
    db = request.app.state.db
    runs = await db['distributed_runs'].find({'business_id': business.id}).sort('created_ts', -1).to_list(length=20)
    return [await distributed.read(db, business.id, row['run_id']) for row in runs]


@router.get('/{run_id}')
async def get(run_id: str, request: Request, business=Depends(get_owned_business)):
    return await distributed.read(request.app.state.db, business.id, run_id)


@router.post('/{run_id}/cancel')
async def cancel(run_id: str, request: Request, business=Depends(get_owned_business)):
    db = request.app.state.db
    run = await db['distributed_runs'].find_one({'_id': run_id, 'business_id': business.id})
    if not run:
        raise HTTPException(404, 'Distributed scenario not found')
    if run['status'] not in {'running', 'cancelled'}:
        raise HTTPException(409, 'Only running analysis may be cancelled; existing proposals are separate')
    await distributed.terminate(db, run, 'cancelled')
    return await distributed.read(db, business.id, run_id)


@router.post('/{run_id}/proposal', status_code=201)
async def proposal(run_id: str, request: Request, business=Depends(get_owned_business)):
    db = request.app.state.db
    view = await distributed.read(db, business.id, run_id)
    if view['status'] != 'ready_for_review':
        raise HTTPException(409, 'Complete all role analyses before creating a proposal')
    strategy = view['roles'][-1]['result']
    budget = strategy['recommended_budget_minor']
    if not budget:
        raise HTTPException(409, 'No affordable campaign budget; review financial constraints')
    # Existing CEO, owner, ledger and executor remain authoritative. This never
    # authorizes itself and deliberately binds a stable id across duplicate clicks.
    task = await create_task(db, request.app.state.agent_registry, business,
        'marketing', 'campaign_launch', {'campaign_name': view['input']['campaign_name'],
        'requested_budget': budget / 100}, source='distributed_simulation',
        run_id=run_id, objective=view['input']['goal'],
        task_id='distributed-' + run_id, force_owner_review=True)
    return to_task_out(task)
