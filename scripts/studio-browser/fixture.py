"""Disposable localhost UI fixture. No project DB, providers or live credentials."""
import base64,json,time
from datetime import datetime,timezone
from fastapi import FastAPI,Request,HTTPException
import uvicorn
app=FastAPI()
user={'id':'11111111-1111-4111-8111-111111111111','email':'studio-fixture@example.com','aud':'authenticated','role':'authenticated','created_at':'2026-11-17T00:00:00Z','app_metadata':{'provider':'email','providers':['email']},'user_metadata':{}}
enc=lambda x:base64.urlsafe_b64encode(json.dumps(x).encode()).decode().rstrip('=')
token=enc({'alg':'HS256','typ':'JWT'})+'.'+enc({'sub':user['id'],'aud':'authenticated','exp':int(time.time())+3600})+'.fixture-signature'
now=lambda:datetime.now(timezone.utc).isoformat()
business={'id':'studio-business','company_name':'Orbit Studio · test fixture','industry':'Software'}
tasks=[{'id':'launch-fixture','agent':'marketing','status':'pending_approval','action_type':'dataset_launch','objective':'Introduce the next big idea.','payload':{'campaign':'Product launch','budget_minor':100000,'currency':'USD','synthetic':True},'mode':'simulation','business_id':'studio-business','approval_fingerprint':'fixture-v1','source':'dataset_demo','ceo_authorized':True,'created_at':now()}, {'id':'ops-fixture','agent':'operations','status':'executing','action_type':'resource_request','objective':'Prepare launch capacity','payload':{'synthetic':True},'mode':'simulation','created_at':now()}, {'id':'hr-fixture','agent':'hr','status':'executed','action_type':'recruitment_request','objective':'Review staffing readiness','payload':{'synthetic':True},'mode':'simulation','created_at':now()}]
events=[{'event_id':'e1','event_type':'budget_request','source':'marketing','timestamp':now(),'data':{'synthetic':True}},{'event_id':'e2','event_type':'arbitration_request','source':'finance','timestamp':now(),'data':{'synthetic':True}}]
@app.post('/auth/v1/token')
async def login(request:Request):
 d=await request.json()
 if d.get('email')!=user['email'] or d.get('password')!='fixture-password':raise HTTPException(400,'Invalid fixture credentials')
 return {'access_token':token,'refresh_token':'fixture-only','expires_in':3600,'expires_at':int(time.time())+3600,'token_type':'bearer','user':user}
@app.get('/auth/v1/user')
async def get_user():return user
@app.get('/api/auth/me')
async def me():return user
@app.get('/api/businesses')
async def businesses():return [business]
@app.get('/api/businesses/{bid}')
async def get_business(bid:str):return business
@app.get('/api/businesses/{bid}/agents')
async def agents(bid:str):return {r:{'agent_id':r,'decision_count':i+2,'status':'working' if r=='operations' else 'idle'} for i,r in enumerate(['ceo','finance','marketing','hr','operations'])}
@app.get('/api/businesses/{bid}/tasks')
async def get_tasks(bid:str):return tasks
@app.get('/api/businesses/{bid}/events/boardroom')
@app.get('/api/businesses/{bid}/events')
async def get_events(bid:str):return events
decisions=[]
@app.get('/api/businesses/{bid}/simulation/decision-log')
async def decision_log(bid:str):return decisions
@app.post('/__fixture__/decision-coordination')
async def decision_coordination():
 decisions.append({'_id':'coordination-decision','event_type':'coordination','sender':'hr','receiver':'finance','source':'hr','timestamp':now(),'data':{'message':'Review staffing budget from decision log','synthetic':True}})
 return {'synthetic':True}

@app.get('/api/tasks/{tid}')
async def get_task(tid:str):return next(t for t in tasks if t['id']==tid)
@app.post('/api/tasks/{tid}/{decision}')
async def decide(tid:str,decision:str,request:Request):
 t=next(t for t in tasks if t['id']==tid)
 payload=await request.json()
 if payload.get('expected_fingerprint') != t.get('approval_fingerprint'):raise HTTPException(409,'Proposal changed')
 if t['status']!='pending_approval':raise HTTPException(409,'Task already decided')
 t['status']='executed' if decision=='approve' else 'rejected';t['result']={'synthetic':True}
 return t
@app.post('/auth/v1/logout')
async def logout():return {}

@app.post('/__fixture__/delegate-budget')
async def delegate_budget():
 events.append({'event_id':'durable-budget-fixture','event_type':'task_assigned','source':'ceo','sender':'ceo','receiver':'finance','timestamp':now(),'data':{'title':'Review department budget','task_id':'ceo-budget-fixture','synthetic':True}})
 tasks.append({'id':'ceo-budget-fixture','business_id':'studio-business','agent':'finance','status':'executing','action_type':'budget_request','objective':'Review department budget','payload':{'amount':500,'synthetic':True},'mode':'simulation','source':'ceo','plan_id':'synthetic-ceo-plan','ceo_authorized':True,'created_at':now()})
 return {'synthetic':True}

@app.post('/__fixture__/collaborate')
async def collaborate():
 for i,(sender,receiver) in enumerate([('ceo','marketing'),('marketing','finance'),('finance','operations'),('operations','hr'),('hr','ceo')]):
  events.append({'event_id':f'collaboration-{i}','event_type':'task_handoff','sender':sender,'receiver':receiver,'source':sender,'timestamp':now(),'data':{'synthetic':True,'message':f'Fixture handoff {i+1}: {sender} to {receiver}'}})
 return {'synthetic':True}

# Walkthrough-only plan fixtures. No model, database or provider is used.
business.update(starting_budget=10000, enabled_agents=['ceo','finance','marketing','hr','operations'])
plans=[]
@app.post('/api/businesses')
async def create_demo_business(request:Request):
 data=await request.json()
 business.update(company_name=data.get('company_name','Orbit Studio · demo'), industry=data.get('industry','Software'))
 return business
@app.get('/api/businesses/{bid}/ceo/plans')
async def get_plans(bid:str):return plans
@app.post('/api/businesses/{bid}/ceo/plans')
async def propose_demo_plan(bid:str,request:Request):
 data=await request.json()
 plan={'plan_id':'demo-plan','goal':data['goal'],'strategy':'Synthetic demo plan: review the campaign before any execution.','status':'draft','created_at':now(),'assignments':[{'department':'marketing','action_type':'campaign_launch','objective':'Introduce the next big idea.','success_criteria':'Review the proposed launch budget and record the simulated result.','payload':{'budget':1000,'synthetic':True}}]}
 plans.append(plan)
 return plan
@app.post('/api/businesses/{bid}/ceo/plans/{pid}/activate')
async def activate_demo_plan(bid:str,pid:str):
 plans[0]['status']='active'
 return {'status':'active','synthetic':True}
@app.get('/api/businesses/{bid}/ceo/reports')
async def demo_reports(bid:str):return []
@app.get('/api/businesses/{bid}/finances')
async def demo_finances(bid:str):return {'available':10000,'revenue':0,'expenses':0,'monthly_payroll_commitment':0}

for task in tasks:
 task.setdefault('source','demo_fixture')
 task.setdefault('business_id','studio-business')
 task.setdefault('ceo_authorized',True)

if __name__=='__main__':uvicorn.run(app,host='127.0.0.1',port=8012)
