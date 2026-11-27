"""Bounded authorized structured lookups plus the existing department-filtered RAG."""
from . import knowledge,retail_data
from .workflow_roles import require_role

async def load(db,business,role,question):
    require_role(business,role)
    account=await db['financial_accounts'].find_one({'_id':business.id})
    profile=await db['business_profiles'].find_one({'business_id':business.id}) or {}
    dataset=await db['demo_datasets'].find_one({'business_id':business.id,'active':True},sort=[('created_at',-1)])
    tasks=await db['tasks'].find({'business_id':business.id}).sort('created_at',-1).to_list(length=200)
    retail=await retail_data.latest(db,business.id)
    result={'company':business.company_name,'industry':business.industry,'facts':[],'tasks':[], 'currency':profile.get('finance',{}).get('currency','USD'),'brand':{k:str(v)[:1200] for k,v in profile.get('brand',{}).items()},'product':{k:str(v)[:1200] for k,v in profile.get('product',{}).items()},'capacity':business.workforce.model_dump() if business.workforce else None,'retrieval_mode':'no_documents'}
    if account:
        available=account['cash_minor']-account['reserved_minor'];result['available_minor']=available
        result['facts'].append({'id':'ledger:available','label':'Available simulated balance','value_minor':available,'currency':result['currency'],'basis':'saved ledger, not real bank cash'})
    if dataset:
        data=dataset['data'];result['goals']=data['goals'];result['catalog']=data['inventory'];result['dataset_id']=data['dataset_id']
        result['facts'].append({'id':'dataset:goals','label':'Fictional startup goals and dates','value':data['goals'],'basis':'synthetic dataset'})
        result['capacity']={'staffed_units_per_day':data['company']['staffed_units_per_day'],'basis':'synthetic planning capacity'}
    if retail:
        summary={**retail['summary'],'products':retail['summary']['products'][:10]};result['retail']=summary
        result['facts'].append({'id':'retail:summary','label':'Historical retail slice','value':summary,'basis':retail['source_claim']})
    result['loaded_task_count']=len(tasks)
    for task in tasks[:30]:
        result['tasks'].append({k:task.get(k) for k in ['task_id','agent','objective','status','plan_id','due_at','owner_feedback','action_type']})
        if task.get('due_at'):result['facts'].append({'id':'deadline:'+task['task_id'],'label':task.get('objective'),'value':task['due_at'],'basis':'saved task deadline'})
    if role=='ceo':
        ids=[t.get('payload',{}).get('submission_id') for t in tasks if t['action_type']=='agent_brief' and t.get('payload',{}).get('submission_id')]
        submitted=await db['agent_artifacts'].find({'business_id':business.id,'owner_id':business.owner_user_id,'artifact_id':{'$in':ids},'kind':'recommendation'},{'image_bytes':0}).to_list(length=20)
        result['department_submissions']=[{'artifact_id':a['artifact_id'],'agent':a['agent'],'task_id':a['task_id'],'recommendation':a['recommendation']} for a in submitted]
    result['facts']=result['facts'][:30]
    retrieval=await knowledge.search(db,business.id,role,question[:1000],3)
    result['retrieval_mode']=retrieval.get('mode','retrieval')
    result['sources']=[{k:s[k] for k in ['chunk_id','document_id','version','title','text']} for s in retrieval.get('results',[])]
    result['facts'] += [{'id':s['chunk_id'],'label':s['title'],'value':s['text'][:1600],'basis':'authorized reference document; not live financial state'} for s in result['sources']]
    return result
