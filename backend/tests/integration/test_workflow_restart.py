"""Shared conversations, brief artifacts and image jobs survive real Mongo reconnect.
Only runs on an explicitly configured disposable integration server/database.
"""
import asyncio,io,os
from datetime import datetime,timedelta,timezone
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pymongo import MongoClient
from app.main import app
from app.config import settings
from app.services import jobs,workflow_images


def test_shared_artifacts_assignments_and_images_survive_real_mongo_restart(monkeypatch):
    uri=os.environ.get('MONGODB_INTEGRATION_URL')
    if not uri:pytest.skip('MONGODB_INTEGRATION_URL required; never uses the configured user database')
    name='shared_workflow_test_'+uuid4().hex;control=MongoClient(uri,serverSelectionTimeoutMS=5000);control.admin.command('ping')
    monkeypatch.setattr(settings,'mongodb_url',uri);monkeypatch.setattr(settings,'mongodb_db_name',name);monkeypatch.setattr(settings,'background_jobs_enabled',True);monkeypatch.setattr(settings,'openai_api_key','fixture-only')
    monkeypatch.setattr(settings,'rag_dense_enabled',False);monkeypatch.setattr(settings,'rag_reranker_enabled',False)
    async def idle(app):await asyncio.Event().wait()
    monkeypatch.setattr(jobs,'worker_loop',idle)
    async def generated(*args,**kwargs):
        out=io.BytesIO();Image.new('RGB',(32,32),'purple').save(out,'PNG');return out.getvalue(),'mock-image-provider'
    monkeypatch.setattr(workflow_images,'generate',generated)
    try:
        with TestClient(app) as first:
            assert first.get('/health').json()['mongo']=='connected'
            first.post('/api/auth/register',json={'email':'restart-workflow@example.com','password':'fixture-restart-password'})
            h={'Authorization':'Bearer '+first.post('/api/auth/login',json={'email':'restart-workflow@example.com','password':'fixture-restart-password'}).json()['access_token']}
            bid=first.post('/api/businesses',headers=h,json={'company_name':'Synthetic restart launch','industry':'Software','starting_budget':300}).json()['id'];root=f'/api/businesses/{bid}/workflow'
            plan=first.post(root+'/launch/plans',headers=h,json={'request_id':str(uuid4()),'goal':'Review and deliver the synthetic desk kit launch.','due_at':(datetime.now(timezone.utc)+timedelta(days=7)).isoformat()}).json()
            assert first.post(root+f'/launch/plans/{plan["plan_id"]}/activate',headers=h,json={'expected_revision':0}).status_code==200
            tasks=first.get(f'/api/businesses/{bid}/tasks',headers=h).json();drafts={}
            for role in ['ceo','finance','marketing','operations','strategy']:
                task=next((t for t in tasks if t['agent']==role),None)
                result=first.post(root+f'/{role}/drafts',headers=h,json={'request_id':str(uuid4()),'content':'Synthetic owner-authored review draft.','task_id':task['id'] if task else None,'recommendation':{'what':'Review the synthetic launch.','why_now':'Confirm saved evidence before approving.','decision_needed':'Owner review required.'}});assert result.status_code==200,result.text;drafts[role]=result.json()['artifact_id']
            image_ids={}
            for role in ['marketing','strategy']:
                task=next(t for t in tasks if t['agent']==role)
                queued=first.post(root+f'/{role}/images',headers=h,json={'request_id':str(uuid4()),'brief':'Fictional desk kit in purple and beige.','task_id':task['id']});assert queued.status_code==200,queued.text
                async def work():return await jobs.run_once(first.app.state.db,first.app.state.agent_registry)
                result=first.portal.call(work);assert result['status']=='succeeded';image_ids[role]=result['result']['artifact_id']
            selected=next(t for t in tasks if t['agent']=='strategy')
            submit=first.post(root+f'/launch/tasks/{selected["id"]}/submit',headers=h,json={'artifact_id':drafts['strategy'],'image_artifact_ids':[image_ids['strategy']],'expected_fingerprint':selected['approval_fingerprint']});assert submit.status_code==200,submit.text
        with TestClient(app) as second:
            assert second.get('/api/auth/me',headers=h).status_code==200
            state=second.get(root+'/launch/state',headers=h).json();assert len(state['tasks'])==4
            for role in drafts:
                history=second.get(root+f'/{role}/conversation',headers=h).json();assert drafts[role] in [a['artifact_id'] for a in history['artifacts']]
            for role,identity in image_ids.items():
                assert second.get(root+f'/{role}/artifacts/{identity}/image?download=true',headers=h).status_code==200
            approved=second.post(f'/api/tasks/{selected["id"]}/approve',headers=h,json={'expected_fingerprint':submit.json()['approval_fingerprint'],'defer_execution':True});assert approved.status_code==200,approved.text
            async def finish():return await jobs.run_once(second.app.state.db,second.app.state.agent_registry)
            result=second.portal.call(finish);assert result['status']=='succeeded',result
            saved=second.get(f'/api/tasks/{selected["id"]}',headers=h).json();assert saved['status']=='executed';assert saved['result']['artifact_id']==drafts['strategy']
    finally:control.drop_database(name);control.close()
