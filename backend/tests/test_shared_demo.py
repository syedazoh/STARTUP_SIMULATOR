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
