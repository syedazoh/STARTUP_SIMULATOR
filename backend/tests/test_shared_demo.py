from tests.test_businesses import client,_register_and_login,_auth_headers

def test_demo_is_separate_idempotent_and_consistent(client):
    owner=_auth_headers(_register_and_login(client,'demo-workflow-owner@example.com'))
    real=client.post('/api/businesses',headers=owner,json={'company_name':'Existing business','industry':'Software','starting_budget':900}).json()
    first=client.post('/api/workflow-demo',headers=owner);assert first.status_code==200,first.text
    second=client.post('/api/workflow-demo',headers=owner);assert second.status_code==200,second.text;assert first.json()['business_id']==second.json()['business_id'];assert first.json()['business_id']!=real['id']
    companies=client.get('/api/businesses',headers=owner).json();assert len(companies)==2
    bid=first.json()['business_id'];finance=client.get(f'/api/businesses/{bid}/finances',headers=owner).json();assert finance['available']==300
    original=client.get(f'/api/businesses/{real["id"]}',headers=owner).json();assert original['starting_budget']==900
    profile=client.get(f'/api/businesses/{bid}/profile',headers=owner).json();assert 'remote teams' in profile['brand']['target_audience']
    assert client.get(f'/api/businesses/{bid}/tasks',headers=owner).json()==[]


def test_operations_capacity_uses_saved_units_without_model_arithmetic(client,monkeypatch):
    from uuid import uuid4
    from app.services import agent_workflow
    def forbidden():raise AssertionError('Capacity arithmetic must not call a model')
    monkeypatch.setattr(agent_workflow,'get_groq_llm',forbidden)
    owner=_auth_headers(_register_and_login(client,'capacity-demo@example.com'))
    bid=client.post('/api/workflow-demo',headers=owner).json()['business_id']
    reply=client.post(f'/api/businesses/{bid}/workflow/operations/turns',headers=owner,json={'request_id':str(uuid4()),'content':'How many working days do 50 kits require?'});assert reply.status_code==200,reply.text
    result=reply.json();assert result['source']=='structured_records';assert '3 staffed working days' in result['reply']['spoken_response'];assert 'calendar' in result['reply']['spoken_response']
    assert 'dataset:capacity' in result['reply']['recommendation']['evidence_ids']

    assert agent_workflow.record_reply('operations','How many people should we hire?',{'capacity':{'staffed_units_per_day':20},'goals':[{'target_units':50}]},None,[]) is None
