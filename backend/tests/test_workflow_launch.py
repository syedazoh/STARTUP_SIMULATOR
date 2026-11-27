from datetime import datetime,timezone,timedelta
from uuid import uuid4
from tests.test_agent_workflow import client,setup,send,Model
from app.services import agent_workflow as workflow

def test_four_linked_assignments_revision_and_exact_owner_approval(client,monkeypatch):
    owner,other,bid,root=setup(client);model=Model();monkeypatch.setattr(workflow,'get_groq_llm',lambda:model)
    body={'request_id':str(uuid4()),'goal':'Launch the fictional desk kit with reviewed departmental briefs.','due_at':(datetime.now(timezone.utc)+timedelta(days=7)).isoformat()}
    plan=client.post(root+'/launch/plans',headers=owner,json=body);assert plan.status_code==200,plan.text;pid=plan.json()['plan_id']
    activate=root+f'/launch/plans/{pid}/activate';one=client.post(activate,headers=owner,json={'expected_revision':0});assert one.status_code==200,one.text
    assert client.post(activate,headers=owner,json={'expected_revision':0}).status_code==200
    tasks=client.get(f'/api/businesses/{bid}/tasks',headers=owner).json();assert len(tasks)==4;assert {t['agent'] for t in tasks}=={'strategy','finance','marketing','operations'}
    task=next(t for t in tasks if t['agent']=='strategy');tid=task['id'];approval=f'/api/tasks/{tid}/approve';assert client.post(approval,headers=owner,json={'expected_fingerprint':task['approval_fingerprint']}).status_code==409
    answer=send(client,root,owner,'strategy','Compare launch positioning.',task_id=tid).json();submission={'artifact_id':answer['artifact_id'],'expected_fingerprint':task['approval_fingerprint']}
    submit=root+f'/launch/tasks/{tid}/submit';saved=client.post(submit,headers=owner,json=submission);assert saved.status_code==200,saved.text;first=saved.json()
    assert client.post(submit,headers=owner,json=submission).status_code==200
    assert client.post(f'/api/tasks/{tid}/request-changes',headers=owner,json={'owner_feedback':'Focus the positioning on small remote teams.','expected_fingerprint':first['approval_fingerprint']}).status_code==200
    assert client.post(approval,headers=owner,json={'expected_fingerprint':first['approval_fingerprint']}).status_code==409
    current=client.get(f'/api/tasks/{tid}',headers=owner).json()
    draft={**answer['reply']['recommendation'],'what':'Validate positioning for small remote teams.'}
    revised=client.post(root+'/strategy/drafts',headers=owner,json={'request_id':str(uuid4()),'content':'Owner revised positioning.','task_id':tid,'reference_id':answer['artifact_id'],'recommendation':draft});assert revised.status_code==200,revised.text
    new=client.post(submit,headers=owner,json={'artifact_id':revised.json()['artifact_id'],'expected_fingerprint':current['approval_fingerprint']});assert new.status_code==200,new.text
    approved=client.post(approval,headers=owner,json={'expected_fingerprint':new.json()['approval_fingerprint']});assert approved.status_code==200,approved.text;assert approved.json()['status']=='executed';assert approved.json()['result']['artifact_id']==revised.json()['artifact_id']
    state=client.get(root+'/launch/state',headers=owner).json();assert len(state['tasks'])==4;assert len([a for a in state['submissions'] if a['task_id']==tid])==2
    assert client.get(root+'/launch/state',headers=other).status_code==403
    assert client.post(submit,headers=other,json=submission).status_code==403

def test_revision_cannot_overwrite_a_concurrent_material_change(client,monkeypatch):
    owner,other,bid,root=setup(client);monkeypatch.setattr(workflow,'get_groq_llm',lambda:Model())
    plan=client.post(root+'/launch/plans',headers=owner,json={'request_id':str(uuid4()),'goal':'Review a bounded fictional launch.','due_at':(datetime.now(timezone.utc)+timedelta(days=7)).isoformat()}).json()
    assert client.post(root+f'/launch/plans/{plan["plan_id"]}/activate',headers=owner,json={'expected_revision':0}).status_code==200
    task=next(t for t in client.get(f'/api/businesses/{bid}/tasks',headers=owner).json() if t['agent']=='strategy')
    answer=send(client,root,owner,'strategy','Compare launch positioning.',task_id=task['id']).json()
    from app.services import workflow_launch
    original=workflow_launch.validate_brief
    async def interleave(db,business,proposal,require_submission=False):
        result=await original(db,business,proposal,require_submission)
        await db['tasks'].update_one({'task_id':task['id']},{'$set':{'revision':9}})
        return result
    monkeypatch.setattr(workflow_launch,'validate_brief',interleave)
    response=client.post(root+f'/launch/tasks/{task["id"]}/submit',headers=owner,json={'artifact_id':answer['artifact_id'],'expected_fingerprint':task['approval_fingerprint']})
    assert response.status_code==409,response.text
    saved=client.get(f'/api/tasks/{task["id"]}',headers=owner).json();assert saved['payload']['submission_id'] is None
