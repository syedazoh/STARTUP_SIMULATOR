"""Saved plan → one internal draft task. No model or social-provider effects."""
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from tests.test_businesses import client,_register_and_login,_auth_headers


def setup(client):
    owner=_auth_headers(_register_and_login(client,'rec-owner@example.com'));other=_auth_headers(_register_and_login(client,'rec-other@example.com'))
    business=client.post('/api/businesses',headers=owner,json={'company_name':'Saved Startup','industry':'Software','starting_budget':1000}).json()
    root=f"/api/businesses/{business['id']}"
    return owner,other,root

def draft():return {'request_id':str(uuid4()),'agent':'marketing','caption_a':'Our first draft.','caption_b':'Help shape our next step.','selected_caption':'b','audience':'Developers','rationale':'Ask for feedback before spending.','promotion_budget':100,'platform':'instagram'}

def test_persisted_revision_review_and_exactly_one_task_after_repeated_approval(client,monkeypatch):
    owner,other,root=setup(client);payload=draft();created=client.post(root+'/recommendations',headers=owner,json=payload);assert created.status_code==200,created.text
    plan=created.json();pid=plan['plan_id'];assert plan['proposed_by']=='marketing';assert plan['evidence']['available_simulated_units']==1000
    assert '100.00' in plan['contributions'][1]['text'];assert client.post(root+'/recommendations',headers=owner,json=payload).json()['plan_id']==pid
    assert client.post(root+'/recommendations',headers=owner,json={**payload,'caption_a':'Changed'}).status_code==409
    assert client.get(root+'/recommendations',headers=other).status_code==403
    assert client.post(root+f'/ceo/plans/{pid}/activate',headers=owner).status_code==409,'Generic plan activation must not bypass recommendation revision checks'
    review=root+f'/recommendations/{pid}/decision'
    result=client.post(review,headers=owner,json={'expected_revision':0,'decision':'request_changes','feedback':'Make the audience more specific.'});assert result.status_code==200,result.text
    assert result.json()['status']=='needs_revision';assert client.post(review,headers=owner,json={'expected_revision':0,'decision':'approve'}).status_code==409
    revise=client.put(root+f'/recommendations/{pid}',headers=owner,json={'expected_revision':0,'draft':{k:v for k,v in {**payload,'audience':'Small software teams'}.items() if k not in {'request_id','agent'}}});assert revise.status_code==200,revise.text
    assert revise.json()['revision']==1;assert revise.json()['feedback'][0]['text']=='Make the audience more specific.'
    assert client.post(review,headers=owner,json={'expected_revision':0,'decision':'approve'}).status_code==409
    def approve():return client.post(review,headers=owner,json={'expected_revision':1,'decision':'approve','feedback':'The revised internal draft is suitable for review.'})
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(lambda _:approve(),range(2)))
    assert any(r.status_code==200 for r in responses);assert all(r.status_code in {200,409} for r in responses)
    tasks=client.get(root+'/tasks',headers=owner).json();assert len(tasks)==1;task=tasks[0];assert task['action_type']=='social_draft';assert task['agent']=='marketing';assert task['status']=='pending_approval';assert task['payload']['caption']==payload['caption_b'];assert task['ceo_review']['basis']=='ceo_plan'
    saved=client.get(root+'/recommendations',headers=owner).json()[0];assert saved['task_ids']==[task['id']]
    assert approve().status_code==200;assert len(client.get(root+'/tasks',headers=owner).json())==1
    current=client.get('/api/tasks/'+task['id'],headers=owner).json();before=client.get(root+'/finances',headers=owner).json()['available']
    executed=client.post('/api/tasks/'+task['id']+'/approve',headers=owner,json={'expected_fingerprint':current['approval_fingerprint']});assert executed.status_code==200,executed.text
    assert executed.json()['result']['published'] is False;assert executed.json()['result']['draft']['platform']=='instagram';assert executed.json()['result']['financial_amount']==0
    assert client.get(root+'/finances',headers=owner).json()['available']==before


def test_rejection_affordability_and_advisory_roles(client):
    owner,other,root=setup(client);payload=draft();payload['promotion_budget']=2000
    plan=client.post(root+'/recommendations',headers=owner,json=payload).json();review=root+f"/recommendations/{plan['plan_id']}/decision"
    assert client.post(review,headers=owner,json={'expected_revision':0,'decision':'approve'}).status_code==409
    assert client.post(review,headers=owner,json={'expected_revision':0,'decision':'reject','feedback':'Promotion exceeds the available balance.'}).status_code==200
    assert client.get(root+'/tasks',headers=owner).json()==[]
    for role in ['ceo','finance','hr','operations']:
        note=client.post(root+'/recommendations',headers=owner,json={'request_id':str(uuid4()),'agent':role});assert note.status_code==200,note.text
        assert note.json()['assignments']==[];assert note.json()['recommendation']['decision_needed']


def test_interrupted_assignment_recovers_the_same_task_without_replaying_effects(client,monkeypatch):
    from app.services import tasks
    owner,other,root=setup(client);plan=client.post(root+'/recommendations',headers=owner,json=draft()).json();pid=plan['plan_id'];review=root+f'/recommendations/{pid}/decision';original=tasks.create_task
    async def interrupted(*args,**kwargs):
        await original(*args,**kwargs)
        raise RuntimeError('Injected lost response after persistence')
    monkeypatch.setattr(tasks,'create_task',interrupted)
    assert client.post(review,headers=owner,json={'expected_revision':0,'decision':'approve'}).status_code==409
    assert len(client.get(root+'/tasks',headers=owner).json())==1
    monkeypatch.setattr(tasks,'create_task',original)
    retry=client.post(review,headers=owner,json={'expected_revision':0,'decision':'approve'});assert retry.status_code==200,retry.text
    assert len(retry.json()['task_ids'])==1;assert len(client.get(root+'/tasks',headers=owner).json())==1
