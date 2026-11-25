"""Recommendations are existing CEO plans, not a second task/approval store."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from ..database.utils import find_one
from ..models.recommendation_schemas import DraftContent
from . import ledger
from .audit import record_audit
from .supervision import activate_plan


def public(doc):return {k:v for k,v in doc.items() if k!='_id'}
def digest(value):return sha256(json.dumps(value,sort_keys=True,default=str,ensure_ascii=False).encode()).hexdigest()

async def evidence(db,registry,business):
    runtime=await registry.get_or_create(business)
    account=await ledger.account_for(db,business,runtime)
    tasks=await db['tasks'].find({'business_id':business.id}).sort('created_at',-1).to_list(length=200)
    counts={role:sum(t['agent']==role for t in tasks) for role in ('ceo','finance','marketing','hr','operations')}
    pending=sum(t['status']=='pending_approval' for t in tasks)
    return {'available_simulated_units':ledger.amount(ledger.available(account)),'workload':counts,'loaded_tasks':len(tasks),'pending_owner':pending,'reported_team':business.workforce.model_dump() if business.workforce else None,'as_of':datetime.now(timezone.utc).isoformat(),'limit':200}


def describe(business,agent,proof,draft):
    if agent=='marketing':
        a=draft.caption_a or f'Meet {business.company_name}. Explore what we are building in {business.industry}. What would help you most?'
        b=draft.caption_b or f'Help shape the next step for {business.company_name}. Share what you would like to see from a business in {business.industry}.'
        audience=draft.audience or f'People interested in {business.industry} (suggested audience, not measured targeting)'
        rationale=draft.rationale or 'Review an organic draft and collect feedback before committing promotion spend.'
        selected=a if draft.selected_caption=='a' else b
        rec={'what':f'Review a {draft.platform.title()} draft for {business.company_name}.','why_now':f"There are {proof['pending_owner']} owner decisions in the loaded task snapshot. This draft can be reviewed without publishing or spending.",'decision_needed':'Approve this recommendation plan, request a revision, or reject it. Task execution still requires the existing owner approval.','caption_a':a,'caption_b':b,'selected_caption':draft.selected_caption,'audience':audience,'rationale':rationale,'promotion_budget':draft.promotion_budget,'platform':draft.platform}
        assignments=[{'department':'marketing','action_type':'social_draft','payload':{'platform':draft.platform,'caption':selected,'audience':audience,'rationale':rationale},'objective':f'Reviewable {draft.platform} draft for {business.company_name}','success_criteria':'Save an internal draft artifact; publish nothing and spend nothing.'}]
    else:
        count=proof['workload'][agent]
        what={'finance':'Review available funds before approving new spending.','operations':'Review recorded workload before adding delivery commitments.','hr':'Compare reported staffing with pending requests before proposing hiring.','ceo':'Prioritize pending owner decisions and coordinate the next plan.'}[agent]
        why=f"{proof['loaded_tasks']} tasks are loaded for this business; {count} belong to {agent.upper() if agent in {'hr','ceo'} else agent.title()}. Available simulated funds: {proof['available_simulated_units']:,.2f} units."
        if agent=='hr':why+=' '+('The employee breakdown is owner-reported context, not live HR headcount.' if proof['reported_team'] else 'No employee breakdown has been saved; ask the owner before assuming department staffing.')
        rec={'what':what,'why_now':why,'decision_needed':'Record your review, then use the department’s existing proposal form for a specific action. This advisory note creates no executable task.'}
        assignments=[]
    return rec,assignments

async def create(db,registry,business,payload):
    if payload.agent not in business.enabled_agents or 'ceo' not in business.enabled_agents:raise HTTPException(409,'Enable this role and CEO first')
    request_hash=digest(payload.model_dump(exclude={'request_id'}))
    plan_id=digest(['recommendation-v1',business.id,str(payload.request_id)])
    existing=await find_one(db['ceo_plans'],{'_id':plan_id,'business_id':business.id})
    if existing:
        if existing.get('request_hash')!=request_hash:raise HTTPException(409,'Request key was reused for different recommendation content')
        return public(existing)
    proof=await evidence(db,registry,business)
    recommendation,assignments=describe(business,payload.agent,proof,payload)
    contributions=[{'agent':payload.agent,'basis':'owner draft' if payload.caption_a or payload.caption_b else 'structured template, not an AI-generated claim','text':recommendation['why_now']}]
    if payload.agent=='marketing':
        requested=payload.promotion_budget;available=proof['available_simulated_units']
        contributions.append({'agent':'finance','basis':'authorized simulated ledger','text':f'Proposed promotion: {requested:,.2f} units; available: {available:,.2f} units. '+('No paid promotion was proposed.' if requested==0 else 'The proposal fits the current balance.' if requested<=available else 'The proposal exceeds the current balance.')+' This draft action spends nothing.'})
    doc={'_id':plan_id,'plan_id':plan_id,'business_id':business.id,'origin':'agent_recommendation','proposed_by':payload.agent,'request_hash':request_hash,'goal':recommendation['what'],'strategy':recommendation['rationale'] if payload.agent=='marketing' else recommendation['why_now'],'status':'draft','revision':0,'recommendation':recommendation,'contributions':contributions,'evidence':proof,'assignments':assignments,'feedback':[],'task_ids':[],'created_at':datetime.now(timezone.utc),'ceo_decision':None}
    try:await db['ceo_plans'].insert_one(doc)
    except DuplicateKeyError:
        existing=await find_one(db['ceo_plans'],{'_id':plan_id,'business_id':business.id})
        if existing.get('request_hash')!=request_hash:raise HTTPException(409,'Request key conflicts with saved content')
        return public(existing)
    await record_audit(db,business.owner_user_id,business.id,'recommendation_created',target_id=plan_id)
    return public(doc)

async def get(db,business,plan_id):
    doc=await find_one(db['ceo_plans'],{'plan_id':plan_id,'business_id':business.id,'origin':'agent_recommendation'})
    if not doc:raise HTTPException(404,'Recommendation not found')
    return doc

async def list_saved(db,business):
    docs=await db['ceo_plans'].find({'business_id':business.id,'origin':'agent_recommendation'}).sort('created_at',-1).to_list(length=50)
    return [public(d) for d in docs]

async def decide(db,registry,business,plan_id,payload):
    doc=await get(db,business,plan_id)
    if payload.expected_revision!=doc['revision']:raise HTTPException(409,'Recommendation changed; review the latest revision')
    if payload.decision=='approve':
        if doc['status'] in {'active','completed'}:return public(doc)
        if doc['proposed_by']=='marketing' and doc['recommendation']['promotion_budget']>0:
            current=await evidence(db,registry,business)
            if doc['recommendation']['promotion_budget']>current['available_simulated_units']:raise HTTPException(409,'Finance: proposed promotion exceeds the currently available simulated balance. Revise it first.')
        return await activate_plan(db,registry,business,plan_id,expected_revision=payload.expected_revision,decision_feedback=payload.feedback)
    if not payload.feedback:raise HTTPException(422,'Give a reason or revision feedback')
    status='needs_revision' if payload.decision=='request_changes' else 'rejected'
    changed=await db['ceo_plans'].find_one_and_update({'plan_id':plan_id,'business_id':business.id,'revision':payload.expected_revision,'status':'draft'},{'$set':{'status':status,'ceo_decision':{'decision':payload.decision,'reason':payload.feedback,'basis':'owner_recorded_ceo_review','actor_id':business.owner_user_id,'at':datetime.now(timezone.utc)}},'$push':{'feedback':{'revision':doc['revision'],'text':payload.feedback,'decision':payload.decision,'at':datetime.now(timezone.utc)}}},return_document=ReturnDocument.AFTER)
    if not changed:raise HTTPException(409,'Recommendation is no longer awaiting review')
    await record_audit(db,business.owner_user_id,business.id,'recommendation_reviewed',target_id=plan_id)
    return public(changed)

async def revise(db,registry,business,plan_id,payload):
    doc=await get(db,business,plan_id)
    if doc['proposed_by']!='marketing':raise HTTPException(422,'Use the existing department proposal form for a new advisory action')
    proof=await evidence(db,registry,business);recommendation,assignments=describe(business,'marketing',proof,payload.draft)
    changed=await db['ceo_plans'].find_one_and_update({'plan_id':plan_id,'business_id':business.id,'revision':payload.expected_revision,'status':{'$in':['draft','needs_revision']}},{'$set':{'recommendation':recommendation,'assignments':assignments,'evidence':proof,'strategy':recommendation['rationale'],'status':'draft','ceo_decision':None,'contributions':[{'agent':'marketing','basis':'owner revision','text':recommendation['rationale']},{'agent':'finance','basis':'authorized simulated ledger','text':f"Proposed promotion: {recommendation['promotion_budget']:,.2f} units; available: {proof['available_simulated_units']:,.2f} units. Draft execution spends nothing."}]},'$inc':{'revision':1}},return_document=ReturnDocument.AFTER)
    if not changed:raise HTTPException(409,'Recommendation changed or has already been activated; reload before editing')
    return public(changed)
