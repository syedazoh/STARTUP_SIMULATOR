"""Explicit creation/reopening of one designated fictional business per owner. No reset of real records."""
import json
from pathlib import Path
from uuid import uuid5,NAMESPACE_URL
from datetime import datetime,timezone
from fastapi import HTTPException
from ..models.demo_dataset import Dataset
from ..models.automation_schemas import DocumentIn
from . import demo_dataset,ledger,knowledge
from ..config import settings

async def create(request,user):
    db=request.app.state.db
    identity=str(uuid5(NAMESPACE_URL,'startup-shared-demo-v2:'+user.id))
    sample=Dataset.model_validate_json((Path(__file__).resolve().parents[1]/'data/shared-launch-v2.json').read_text())
    roles=['ceo','finance','marketing','operations','strategy'];now=datetime.now(timezone.utc)
    doc={'_id':identity,'business_id':identity,'owner_user_id':user.id,'company_name':sample.company.name,'industry':'Fictional desk kits','starting_budget':sample.company.starting_capital_minor/100,'starting_customer_base':0,'starting_headcount':5,'starting_resources':150,'enabled_agents':roles,'created_at':now,'demo_namespace':'shared-launch-v2','workforce':{'total_headcount':5,'positions':[{'department':'Operations','role':'Fictional packer','count':2,'employment_type':'full_time'},{'department':'Engineering','role':'Fictional designer','count':2,'employment_type':'full_time'},{'department':'Marketing','role':'Fictional campaign planner','count':1,'employment_type':'part_time'}]}}
    inserted=await db['businesses'].update_one({'_id':identity},{'$setOnInsert':doc},upsert=True)
    saved=await db['businesses'].find_one({'_id':identity})
    if saved['owner_user_id']!=user.id or saved.get('demo_namespace')!='shared-launch-v2':raise HTTPException(409,'Demo identity conflict; no existing records were changed')
    from ..api.routes.businesses import _to_business_out
    business=_to_business_out(saved)
    profile={'business_id':identity,'brand':{'voice_tone':'Warm, specific and practical','mission_statement':'Fictional desk-kit launch for planning and evaluation','target_audience':'Small remote teams and freelance designers','competitors':[]},'product':{'description':'Fictional Sprout desk kit','pricing_model':'One-off purchase','price_points':[50]},'marketing':{'active_channels':['instagram','facebook'],'posting_frequency':'Drafts only','content_dos':['Be specific','Use deep purple and beige'],'content_donts':['No invented customer results','No certification claims']},'finance':{'monthly_budget_cap':300,'currency':'USD','spend_categories':['simulated launch']},'operations':{'support_hours':'Not yet specified by owner','escalation_policy':'Owner reviews commitments'},'updated_at':now}
    await db['business_profiles'].update_one({'business_id':identity},{'$setOnInsert':profile},upsert=True)
    runtime=await request.app.state.agent_registry.get_or_create(business);await ledger.account_for(db,business,runtime)
    preview=await demo_dataset.preview(db,identity,sample);await demo_dataset.commit_import(db,identity,sample,preview['digest'])
    indexing=[]
    if settings.background_jobs_enabled:
        for reference in sample.references:
            indexing.append(await knowledge.submit_document(db,business,user.id,DocumentIn(key='shared-'+reference.id,title=reference.title,text=reference.text,departments=roles)))
    return {'business_id':identity,'synthetic':True,'reopened':inserted.upserted_id is None,'references_queued':len(indexing),'message':'Fictional demo only. Existing business records and previous demo work are preserved. Enable background jobs to index references and generate images.'}
