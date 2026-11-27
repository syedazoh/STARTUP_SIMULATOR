"""Shared service/model doubles; no live model, account or external action."""
from uuid import uuid4
from tests.test_businesses import client,_register_and_login,_auth_headers
from app.models.workflow_schemas import WorkflowReply,Recommendation,Option
from app.services import agent_workflow as workflow

class Model:
    calls=0
    def with_structured_output(self,schema):return self
    async def ainvoke(self,prompt):
        self.calls+=1;self.prompt=prompt
        return WorkflowReply(spoken_response='Review this scoped draft.',recommendation=Recommendation(what='Review a launch option.',why_now='The saved goal needs a decision.',decision_needed='Ask the owner to review.',options=[Option(title='Small test',description='Validate the proposal.'),Option(title='Wait',description='Collect missing evidence.')],evidence_ids=['invented-id']))
def setup(client):
    owner=_auth_headers(_register_and_login(client,'workflow-owner@example.com'));other=_auth_headers(_register_and_login(client,'workflow-other@example.com'))
    bid=client.post('/api/businesses',headers=owner,json={'company_name':'Workflow fixture','industry':'Software','starting_budget':300}).json()['id']
    return owner,other,bid,f'/api/businesses/{bid}/workflow'
def send(client,root,owner,role,text,**extra):return client.post(f'{root}/{role}/turns',headers=owner,json={'request_id':str(uuid4()),'content':text,**extra})

def test_all_five_share_saved_scoped_recommendations_without_creating_tasks(client,monkeypatch):
    owner,other,bid,root=setup(client);model=Model();monkeypatch.setattr(workflow,'get_groq_llm',lambda:model)
    for role in ['ceo','finance','marketing','operations','strategy']:
        response=send(client,root,owner,role,'Recommend our next launch step.');assert response.status_code==200,response.text
        row=response.json();assert row['artifact_id'];assert row['source']=='model';assert row['reply']['recommendation']['evidence_ids']==[]
        saved=client.get(f'{root}/{role}/conversation',headers=owner).json();assert saved['artifacts'][0]['artifact_id']==row['artifact_id'];assert saved['turns'][0]['turn_id']==row['turn_id']
        assert client.get(f'{root}/{role}/conversation',headers=other).status_code==403
    assert model.calls==5;assert client.get(f'/api/businesses/{bid}/tasks',headers=owner).json()==[]

def test_clarification_scope_budget_and_foreign_references_use_records(client,monkeypatch):
    owner,other,bid,root=setup(client);model=Model();monkeypatch.setattr(workflow,'get_groq_llm',lambda:model)
    unclear=send(client,root,owner,'finance','What is a T?').json();assert unclear['reply']['intent']=='clarify';assert unclear['artifact_id'] is None
    assert send(client,root,owner,'marketing','Give me a pancake recipe').json()['reply']['intent']=='out_of_scope'
    assert send(client,root,owner,'operations','Revise that.').json()['reply']['intent']=='clarify'
    missing=send(client,root,owner,'finance','Can we spend 400 on a campaign?').json();assert missing['reply']['intent']=='missing_data'
    client.get(f'/api/businesses/{bid}/finances',headers=owner)
    answer=send(client,root,owner,'finance','Can we spend $400 on a campaign?').json();assert '100.00' in answer['reply']['spoken_response'];assert '300.00' in answer['reply']['spoken_response'];assert answer['source']=='structured_records'
    assert send(client,root,owner,'finance','Can we spend Rs. 400 on a campaign?').json()['reply']['intent']=='clarify'
    assert send(client,root,owner,'marketing','Revise that.',reference_id=answer['artifact_id']).status_code==404
    assert send(client,root,owner,'finance','Can we spend $'+'9'*1500+' on a campaign?').json()['reply']['intent']=='clarify'
    assert model.calls==0

def test_turn_retry_replays_one_saved_artifact_and_reference_stays_in_conversation(client,monkeypatch):
    owner,other,bid,root=setup(client);model=Model();monkeypatch.setattr(workflow,'get_groq_llm',lambda:model)
    body={'request_id':str(uuid4()),'content':'Recommend a launch option.'};path=root+'/strategy/turns'
    one=client.post(path,headers=owner,json=body);assert one.status_code==200,one.text
    two=client.post(path,headers=owner,json=body);assert two.json()['artifact_id']==one.json()['artifact_id'];assert model.calls==1
    assert client.post(path,headers=owner,json={**body,'content':'Different'}).status_code==409
    revised=send(client,root,owner,'strategy','Compare it with the first option.',reference_id=one.json()['artifact_id']);assert revised.status_code==200,revised.text;assert one.json()['artifact_id'] in model.prompt
    assert len(client.get(root+'/strategy/conversation',headers=owner).json()['artifacts'])==2
