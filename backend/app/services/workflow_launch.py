"""Owner-activated launch uses existing CEO plans, tasks, revisions and approvals."""
from datetime import datetime,timezone
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from .jobs import digest
from .workflow_roles import require_role
from .agent_workflow import artifact,public
from .audit import record_audit
from ..models.task_schemas import approval_fingerprint,to_task_out,TaskRevisionIn

async def create(db,business,payload):
    require_role(business,'ceo')
    for role in ('strategy','finance','marketing','operations'):require_role(business,role)
    identity=digest(['shared-launch',business.id,str(payload.request_id)])
    content=payload.model_dump(mode='json');request_digest=digest(content)
    assignments=[{'department':role,'action_type':'agent_brief','payload':{'request':instruction,'due_at':payload.due_at.isoformat(),'submission_id':None,'image_artifact_ids':[]},'objective':instruction,'success_criteria':'Submit a saved recommendation; owner reviews its exact version.'} for role,instruction in [('strategy','Compare launch positioning options and risks.'),('finance','Compare launch spending with saved available funds.'),('marketing','Propose a brand-aligned campaign and draft visual if requested.'),('operations','Prepare delivery, staffing capacity, dependencies and launch timeline.')]]
    plan={'_id':identity,'plan_id':identity,'business_id':business.id,'origin':'conversational_launch','goal':payload.goal,'strategy':'Coordinate four departmental submissions; owner decisions remain explicit.','status':'draft','revision':0,'assignments':assignments,'task_ids':[],'created_at':datetime.now(timezone.utc),'request_digest':request_digest}
    try:await db['ceo_plans'].insert_one(plan)
    except DuplicateKeyError:
        saved=await db['ceo_plans'].find_one({'_id':identity,'business_id':business.id})
        if saved['request_digest']!=request_digest:raise HTTPException(409,'Launch request ID reused for different content')
        return public(saved)
    await record_audit(db,business.owner_user_id,business.id,'shared_launch_drafted',target_id=identity)
    return public(plan)

async def validate_brief(db,business,task,require_submission=False):
    plan=await db['ceo_plans'].find_one({'business_id':business.id,'plan_id':task.get('plan_id'),'origin':'conversational_launch','status':{'$in':['assigning','active','completed']}})
    if not plan:raise HTTPException(409,'Internal brief requires an owner-activated launch plan')
    original=next((a for a in plan['assignments'] if a['department']==task['agent'] and a['objective']==task.get('objective')),None)
    p=task['payload']
    if not original or any(p.get(k)!=original['payload'].get(k) for k in ['request','due_at']):raise HTTPException(409,'Brief differs from the activated assignment')
    if not p.get('submission_id'):
        if require_submission:raise HTTPException(409,'Wait for a submitted recommendation before approving this task')
        return None
    saved=await artifact(db,business,task['agent'],p['submission_id'])
    if saved['kind']!='recommendation' or saved.get('task_id')!=task['task_id']:raise HTTPException(409,'Submission does not belong to this assignment')
    for image_id in p.get('image_artifact_ids',[]):
        image=await artifact(db,business,task['agent'],image_id)
        if image['kind']!='image' or image.get('task_id')!=task['task_id']:raise HTTPException(409,'Image does not belong to this assignment')
    return saved

async def submit(db,registry,business,task_id,payload,request):
    task=await db['tasks'].find_one({'business_id':business.id,'task_id':task_id,'action_type':'agent_brief'})
    if not task:raise HTTPException(404,'Assignment not found')
    if task['payload'].get('submission_id')==payload.artifact_id and task['payload'].get('image_artifact_ids',[])==payload.image_artifact_ids:return to_task_out(task)
    if approval_fingerprint(task)!=payload.expected_fingerprint:raise HTTPException(409,'Assignment changed; refresh before submitting')
    proposal={**task['payload'],'submission_id':payload.artifact_id,'image_artifact_ids':payload.image_artifact_ids}
    await validate_brief(db,business,{**task,'payload':proposal},True)
    # Reuse existing atomic revision, authorization and fingerprint machinery.
    from ..api.routes.tasks import revise_task
    revised=await revise_task(TaskRevisionIn(payload=proposal),request,{'task':task,'business':business})
    from .collaboration import best_effort_handoff
    await best_effort_handoff(db,business.id,task['agent'],'ceo','submission_received',task['objective'],task_id=task_id,plan_id=task['plan_id'])
    return revised

async def state(db,business):
    plans=await db['ceo_plans'].find({'business_id':business.id,'origin':'conversational_launch'}).sort('created_at',-1).to_list(length=20)
    tasks=await db['tasks'].find({'business_id':business.id,'action_type':'agent_brief'}).sort('created_at',-1).to_list(length=100)
    aids={t['task_id'] for t in tasks}
    submissions=await db['agent_artifacts'].find({'business_id':business.id,'owner_id':business.owner_user_id,'task_id':{'$in':list(aids)}},{'image_bytes':0}).sort('created_at',-1).to_list(length=200)
    return {'plans':[public(p) for p in plans],'tasks':[to_task_out(t).model_dump(mode='json') for t in tasks],'submissions':[public(a) for a in submissions]}
