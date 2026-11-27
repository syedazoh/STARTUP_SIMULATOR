"""One owner-scoped shared conversation API; no identity fields are accepted from clients."""
from fastapi import APIRouter,Depends,Request
from ..deps import get_owned_business
from ...models.workflow_schemas import TurnIn,PlanIn,ActivateIn,SubmissionIn,DraftIn,ImageIn
from ...services import agent_workflow
from ...core.rate_limit import RateLimiter,rate_limit_dependency
router=APIRouter(prefix='/api/businesses/{business_id}/workflow',tags=['agent-workflow'])
limited=Depends(rate_limit_dependency(RateLimiter(max_requests=30,window_seconds=60)))
@router.get('/{role}/conversation')
async def history(role:str,request:Request,business=Depends(get_owned_business)):
    return await agent_workflow.history(request.app.state.db,business,role)
@router.post('/{role}/turns',dependencies=[limited])
async def turn(role:str,payload:TurnIn,request:Request,business=Depends(get_owned_business)):
    return await agent_workflow.turn(request.app.state.db,business,role,payload)

@router.get('/launch/state')
async def launch_state(request:Request,business=Depends(get_owned_business)):
    from ...services.workflow_launch import state
    return await state(request.app.state.db,business)
@router.post('/launch/plans',dependencies=[limited])
async def launch_plan(payload:PlanIn,request:Request,business=Depends(get_owned_business)):
    from ...services.workflow_launch import create
    return await create(request.app.state.db,business,payload)
@router.post('/launch/plans/{plan_id}/activate',dependencies=[limited])
async def activate(plan_id:str,payload:ActivateIn,request:Request,business=Depends(get_owned_business)):
    from ...services.supervision import activate_plan
    from fastapi import HTTPException
    plan=await request.app.state.db['ceo_plans'].find_one({'plan_id':plan_id,'business_id':business.id,'origin':'conversational_launch'})
    if not plan:raise HTTPException(404,'Launch plan not found')
    return await activate_plan(request.app.state.db,request.app.state.agent_registry,business,plan_id,expected_revision=payload.expected_revision)
@router.post('/launch/tasks/{task_id}/submit',dependencies=[limited])
async def submit(task_id:str,payload:SubmissionIn,request:Request,business=Depends(get_owned_business)):
    from ...services.workflow_launch import submit
    return await submit(request.app.state.db,request.app.state.agent_registry,business,task_id,payload,request)

@router.post('/{role}/drafts',dependencies=[limited])
async def manual_draft(role:str,payload:DraftIn,request:Request,business=Depends(get_owned_business)):
    return await agent_workflow.turn(request.app.state.db,business,role,payload,manual=payload.recommendation)

@router.post('/{role}/images',dependencies=[limited])
async def image_job(role:str,payload:ImageIn,request:Request,business=Depends(get_owned_business)):
    from ...services.workflow_images import queue
    return await queue(request.app.state.db,business,role,payload)
@router.get('/{role}/images')
async def images(role:str,request:Request,business=Depends(get_owned_business)):
    from ...services.workflow_roles import require_role
    from ...services.jobs import public
    require_role(business,role)
    jobs=await request.app.state.db['background_jobs'].find({'business_id':business.id,'requested_by':business.owner_user_id,'kind':'agent_image','payload.role':role}).sort('created_ts',-1).to_list(length=30)
    return [public(job) for job in jobs]
@router.get('/{role}/artifacts/{artifact_id}/image')
async def image_content(role:str,artifact_id:str,request:Request,download:bool=False,business=Depends(get_owned_business)):
    from fastapi.responses import Response
    from fastapi import HTTPException
    saved=await agent_workflow.artifact(request.app.state.db,business,role,artifact_id)
    if saved['kind']!='image':raise HTTPException(404,'Image artifact not found')
    return Response(saved['image_bytes'],media_type='image/png',headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff','Content-Disposition':f'{"attachment" if download else "inline"}; filename="draft-{saved["artifact_id"]}.png"'})
