"""Disposable acceptance backend: real app/services, mongomock + a fake local identity provider.
Never deploy this script. It refuses to start without an explicit fixture-only flag.
"""
import os
if os.environ.get('SIMULATOR_FIXTURE_ONLY')!='1':raise SystemExit('Set SIMULATOR_FIXTURE_ONLY=1 only for isolated local acceptance.')
import base64,json,time,secrets
from datetime import datetime,timezone
from contextlib import asynccontextmanager
from cryptography.fernet import Fernet
os.environ.update(GROQ_API_KEY='',SECRET_KEY=secrets.token_urlsafe(40),CREDENTIAL_MASTER_KEY=Fernet.generate_key().decode(),DEBUG='true',MONGODB_URL='mongodb://fixture-only',MONGODB_DB_NAME='nov25_acceptance',CHROMA_PERSIST_DIR='/tmp/nov25-chroma',ALLOWED_ORIGINS='http://localhost:3025,http://localhost:5175',SUPABASE_URL='http://127.0.0.1:8013',SUPABASE_PUBLISHABLE_KEY='fixture-only',BACKGROUND_JOBS_ENABLED='false',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',RAG_ALLOW_MODEL_DOWNLOAD='false')
from mongomock_motor import AsyncMongoMockClient
import app.database.mongodb as mongodb
mongo=AsyncMongoMockClient();mongodb.AsyncIOMotorClient=lambda *a,**kw:mongo
from app.main import app
from app.core.crypto import encrypt_data_key,generate_data_key
from app.core.security import hash_password
from app.services import supabase_auth
from fastapi import Request,HTTPException
import uvicorn
SUBJECT='11111111-1111-4111-8111-111111111111';EMAIL='studio-fixture@example.com'
user={'id':SUBJECT,'email':EMAIL,'aud':'authenticated','role':'authenticated','email_confirmed_at':'2026-11-01T00:00:00Z','created_at':'2026-11-01T00:00:00Z','app_metadata':{'provider':'email','providers':['email']},'user_metadata':{}}
auth_events={'otp_requests':0,'verify_attempts':0,'refreshes':0,'logouts':0};short_session=False
enc=lambda value:base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip('=')
def session(short=False):
    expiry=int(time.time())+(2 if short else 3600)
    token=enc({'alg':'HS256','typ':'JWT'})+'.'+enc({'sub':SUBJECT,'aud':'authenticated','exp':expiry})+'.fixture-signature'
    return {'access_token':token,'refresh_token':'fixture-refresh-only','expires_in':2 if short else 3600,'expires_at':expiry,'token_type':'bearer','user':user}
def verified(token):
    try:
        payload=json.loads(base64.urlsafe_b64decode(token.split('.')[1]+'==='))
        if not token.endswith('.fixture-signature') or payload['sub']!=SUBJECT or payload['exp']<time.time():raise ValueError()
        return SUBJECT,EMAIL
    except Exception:raise HTTPException(401,'Invalid fixture session')
async def verify_identity(token):return verified(token)
supabase_auth.verify_identity=verify_identity
original_lifespan=app.router.lifespan_context
@asynccontextmanager
async def lifespan(application):
    async with original_lifespan(application):
        db=application.state.db;now=datetime.now(timezone.utc)
        for uid,email in [('original-fixture-owner',EMAIL),('other-fixture-owner','other-fixture@example.com')]:
            await db['users'].insert_one({'user_id':uid,'email':email,'hashed_password':hash_password('fixture-password'),'role':'owner','encrypted_data_key':encrypt_data_key(generate_data_key()),'created_at':now})
        await db['auth_identities'].insert_one({'subject':SUBJECT,'user_id':'original-fixture-owner'})
        for bid,owner,name in [('studio-business','original-fixture-owner','Original Fixture Startup'),('other-business','other-fixture-owner','Private Other Startup')]:
            await db['businesses'].insert_one({'business_id':bid,'owner_user_id':owner,'company_name':name,'industry':'Software','starting_budget':10000,'starting_customer_base':20,'starting_headcount':7,'starting_resources':100,'enabled_agents':['ceo','finance','marketing','hr','operations'],'created_at':now})
        for i,(role,status) in enumerate([('marketing','pending_approval'),('operations','executing'),('hr','executed')]):
            await db['tasks'].insert_one({'_id':f'fixture-task-{i}','task_id':f'fixture-task-{i}','business_id':'studio-business','agent':role,'action_type':'campaign_launch' if role=='marketing' else 'resource_request','payload':{'campaign_name':'Existing launch','requested_budget':100} if role=='marketing' else {'resource_type':'Capacity','quantity':1,'unit_cost':0},'source':'fixture','objective':f'Existing {role} work','status':status,'ceo_authorized':True,'ceo_review':{'decision':'approve','basis':'fixture','reason':'Synthetic setup'},'requires_asset':False,'asset_id':None,'created_at':now})
        await db['tasks'].insert_one({'_id':'private-other-task','task_id':'private-other-task','business_id':'other-business','agent':'marketing','action_type':'campaign_launch','status':'pending_approval','objective':'Private other launch','payload':{'campaign_name':'Private other launch','requested_budget':900},'created_at':now})
        yield
app.router.lifespan_context=lifespan
@app.post('/auth/v1/otp')
async def otp(request:Request):
    body=await request.json()
    if body.get('create_user') is not False:raise HTTPException(400,'Fixture requires deliberate separate registration')
    auth_events['otp_requests']+=1
    return {}
@app.post('/auth/v1/verify')
async def verify(request:Request):
    body=await request.json();auth_events['verify_attempts']+=1
    # Synthetic code only; never log request bodies or real verification codes.
    if body.get('email')!=EMAIL or body.get('token')!='100200' or body.get('type')!='email':raise HTTPException(403,'Incorrect or expired fixture code')
    return session(short_session)
@app.post('/auth/v1/token')
async def token(request:Request):
    body=await request.json()
    if request.query_params.get('grant_type')=='refresh_token':
        if body.get('refresh_token')!='fixture-refresh-only':raise HTTPException(401,'Expired fixture refresh')
        auth_events['refreshes']+=1;return session()
    if body.get('email')!=EMAIL or body.get('password')!='fixture-password':raise HTTPException(400,'Invalid fixture credentials')
    return session()
@app.get('/auth/v1/user')
async def get_user(request:Request):
    verified(request.headers.get('authorization','').removeprefix('Bearer '));return user
@app.post('/auth/v1/logout')
async def logout():auth_events['logouts']+=1;return {}
@app.get('/__fixture__/auth-state')
async def auth_state():return auth_events
@app.post('/__fixture__/short-session')
async def shorten():
    global short_session
    short_session=True;return {'synthetic':True}
if __name__=='__main__':uvicorn.run(app,host='127.0.0.1',port=8013,log_level='warning')
