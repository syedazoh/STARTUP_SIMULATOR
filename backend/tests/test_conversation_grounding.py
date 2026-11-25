"""Actual deterministic outputs and a labelled model double; no paid/live model calls."""
from tests.test_chat import client, _auth_headers, _create_business, FakeChatLLM
import app.services.chat as chat
from app.agents.schemas import ChatReply
import json,os
from pathlib import Path


def test_ambiguity_clarification_missing_data_and_scope_do_not_guess_or_call_model(client,monkeypatch):
    fake=FakeChatLLM([]);monkeypatch.setattr(chat,'get_groq_llm',lambda *a,**k:fake)
    headers=_auth_headers(client,'grounding@example.com');bid=_create_business(client,headers)
    def ask(text):
        result=client.post(f'/api/businesses/{bid}/agents/finance/chat',headers=headers,json={'content':text,'screen_context':{'screen':'dashboard','chart':'task_status'}})
        assert result.status_code==200,result.text
        return result.json()
    ambiguous=ask('What is a T?');assert ambiguous['thread']['messages'][-1]['content']=='Where did you see “T” in the simulator?';assert ambiguous['intent']=='clarify';assert ambiguous['task'] is None
    clarified=ask('It is the total in the task-status donut chart.');assert 'number of loaded tasks' in clarified['thread']['messages'][-1]['content'];assert '0' in clarified['thread']['messages'][-1]['content']
    definition=ask('What does runway mean?');assert 'cash' in definition['thread']['messages'][-1]['content'];assert definition['intent']=='answer'
    missing=ask('Can we afford this campaign?');assert missing['intent']=='missing_data';assert 'recorded available balance' in missing['thread']['messages'][-1]['content']
    unrelated=ask('Give me a pancake recipe');assert unrelated['intent']=='out_of_scope';assert 'startup' in unrelated['thread']['messages'][-1]['content'];assert fake.calls==0
    assert all(x['answer_source']=='structured_records' for x in [ambiguous,clarified,definition,missing,unrelated])
    directory=os.environ.get('NOV25_REPORT_DIR')
    if directory:
        Path(directory).mkdir(parents=True,exist_ok=True)
        rows=[{'input':question,'response':result['thread']['messages'][-1]['content'],'source':'actual deterministic service output, no model call'} for question,result in [('What is a T?',ambiguous),('It is the total in the task-status donut chart.',clarified),('What does runway mean?',definition),('Can we afford this campaign?',missing),('Give me a pancake recipe',unrelated)]]
        Path(directory,'conversation-responses.json').write_text(json.dumps(rows,indent=2))


def test_clear_query_uses_authorized_tasks_and_model_followup_gets_bounded_context(client,monkeypatch):
    owner=_auth_headers(client,'owner-queries@example.com');other=_auth_headers(client,'other-queries@example.com');bid=_create_business(client,owner);other_bid=_create_business(client,other)
    # Use the existing proposal path, then query actual saved task state.
    proposal=client.post(f'/api/businesses/{bid}/agents/marketing/actions/campaign-launch',headers=owner,json={'campaign_name':'Our launch','requested_budget':100})
    assert proposal.status_code in (200,201),proposal.text
    client.post(f'/api/businesses/{other_bid}/agents/marketing/actions/campaign-launch',headers=other,json={'campaign_name':'Private other launch','requested_budget':100})
    answer=client.post(f'/api/businesses/{bid}/agents/ceo/chat',headers=owner,json={'content':'Which Marketing tasks are waiting for approval?'}).json()
    text=answer['thread']['messages'][-1]['content'];assert '1 task(s)' in text;assert 'Private other' not in text;assert 'Our launch' in text or proposal.json()['id'] in text
    fake=FakeChatLLM([ChatReply(reply='For this recorded workload, review the pending Marketing proposal first.')]);monkeypatch.setattr(chat,'get_groq_llm',lambda *a,**k:fake)
    result=client.post(f'/api/businesses/{bid}/agents/ceo/chat',headers=owner,json={'content':'How should we prioritize our current business workload?'}).json()
    directory=os.environ.get('NOV25_REPORT_DIR')
    if directory:
        Path(directory,'clear-task-response.json').write_text(json.dumps({'input':'Which Marketing tasks are waiting for approval?','response':text,'source':'actual deterministic service output from authorized saved task, no model call'},indent=2))
        path=Path(directory,'model-double-response.json');path.write_text(json.dumps({'input':'How should we prioritize our current business workload?','response':result['thread']['messages'][-1]['content'],'source':'deterministic FakeChatLLM test double, not live Groq'},indent=2))
    assert result['answer_source']=='model';assert 'Authorized business records' in fake.last_prompt;assert 'Private other launch' not in fake.last_prompt
    assert client.post(f'/api/businesses/{bid}/agents/finance/chat',headers=other,json={'content':'show tasks'}).status_code==403


def test_chat_cannot_claim_an_unsupported_social_publication(client,monkeypatch):
    owner=_auth_headers(client,'draft-only-chat@example.com');bid=_create_business(client,owner)
    fake=FakeChatLLM([ChatReply(reply='Published!',action_requested=True,action_type='instagram_post',action_payload_json='{"content":"Untrusted model request"}')]);monkeypatch.setattr(chat,'get_groq_llm',lambda *a,**k:fake)
    result=client.post(f'/api/businesses/{bid}/agents/marketing/chat',headers=owner,json={'content':'Prepare an Instagram update for our startup.'}).json()
    assert result['task'] is None;assert 'No post was published' in result['thread']['messages'][-1]['content'];assert client.get(f'/api/businesses/{bid}/tasks',headers=owner).json()==[]
