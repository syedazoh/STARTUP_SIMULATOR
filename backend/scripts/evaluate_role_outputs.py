"""Finite synthetic HTTP evaluation, called only inside the isolated release smoke.
No provider/model keys; real API/Mongo/role containers. Not an AI quality claim.
"""
import json
import math
from pathlib import Path
import platform
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class Client:
    def __init__(self):
        self.token = None

    def call(self, path, body=None):
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        request = Request('http://127.0.0.1:8000'+path,
            data=json.dumps(body).encode() if body is not None else None, headers=headers)
        with urlopen(request, timeout=30) as response:
            return json.load(response)


def until(check, timeout=45):
    deadline = time.monotonic()+timeout
    while time.monotonic()<deadline:
        result=check()
        if result:return result
        time.sleep(.5)
    raise AssertionError('Evaluation polling deadline expired')


def evaluate():
    fixture=json.loads((Path(__file__).parents[1]/'tests/fixtures/distributed_eval.json').read_text())
    rows=[]
    original_owner=None
    for case in fixture['cases']:
        client=Client()
        identity={'email':case['id']+'@synthetic.example.com','password':'Local-evaluation-12345'}
        client.call('/api/auth/register',identity)
        client.token=client.call('/api/auth/login',identity)['access_token']
        business=client.call('/api/businesses',{'company_name':'Synthetic '+case['id'],
            'industry':'Software','starting_budget':case['capital_usd']})['id']
        base='/api/businesses/'+business
        first=time.perf_counter();client.call(base+'/finances');first_read_ms=(time.perf_counter()-first)*1000
        if case['policy']:
            for key,department,text in [('policy','support','Launch return policy: product returns require owner review. No automatic refund is promised.'),
                ('private','finance','DO_NOT_RETURN_FINANCE_CONTEXT: confidential finance policy.')]:
                client.call(base+'/knowledge',{'key':key,'title':key,'text':text,'departments':[department]})
            until(lambda: all(d['status']=='ready' for d in client.call(base+'/automation')['documents']))
        started=time.perf_counter()
        run=client.call(base+'/distributed-runs',{'idempotency_key':case['id'],'seed':case['seed'],
            'requested_budget_minor':case['requested_minor']})
        url=base+'/distributed-runs/'+run['run_id']
        def finished():
            result=client.call(url)
            assert result['status'] in {'running','ready_for_review'},result['status']
            return result if result['status']=='ready_for_review' else None
        run=until(finished)
        finance=run['roles'][2]['result'];support=run['roles'][5]['result'];marketing=run['roles'][1]['result']
        budget_ok=finance['recommended_budget_minor']==case['expected_minor']
        support_ok=support['mode']==case['support_mode'] and 'DO_NOT_RETURN_FINANCE_CONTEXT' not in support['artifact']
        if case['policy']:
            support_ok &= bool(support['citations']) and all(c['title']=='policy' and c['quote'] in support['artifact'] for c in support['citations'])
        else:
            support_ok &= not support['citations'] and 'cannot confirm' in support['artifact']
        content_ok=marketing['mode']=='rule_based' and 'Synthetic draft' in marketing['artifact'] and 'no product performance' in marketing['artifact']
        assert budget_ok and support_ok and content_ok
        if original_owner:
            try: original_owner.call(url)
            except HTTPError as exc: assert exc.code==403
            else: raise AssertionError('Cross-business evaluation access leaked')
        else:original_owner=client
        if case['expected_minor']==0:
            try:client.call(url+'/proposal',{})
            except HTTPError as exc:assert exc.code==409
            else:raise AssertionError('Unaffordable campaign was materialized')
        rows.append({'case':case['id'],'actual_budget_minor':finance['recommended_budget_minor'],
            'expected_budget_minor':case['expected_minor'],'budget_pass':budget_ok,'support_pass':bool(support_ok),
            'content_contract_pass':content_ok,'support_mode':support['mode'],
            'baseline_budget_minor':case['requested_minor'],
            'baseline_cash_safe':case['requested_minor']<=round(case['capital_usd']*100),
            'first_new_business_finance_read_ms':round(first_read_ms,3),
            'seven_role_duration_seconds':round(time.perf_counter()-started,3)})
    # The last controlled identity/business stays fixed during these concurrent reads.
    def sample(_):
        started=time.perf_counter()
        try:client.call(base+'/finances');ok=True
        except Exception:ok=False
        return (time.perf_counter()-started)*1000,ok
    with ThreadPoolExecutor(max_workers=4) as pool:samples=list(pool.map(sample,range(100)))
    times=sorted(t for t,ok in samples if ok)
    assert len(times)==100,'Read error rate was nonzero; inspect before acceptance'
    return {'synthetic':True,'python':platform.python_version(),'scenario_cases':len(rows),
        'case_results':rows,'budget_pass':sum(r['budget_pass'] for r in rows),
        'baseline_cash_safe':sum(r['baseline_cash_safe'] for r in rows),
        'support_pass':sum(r['support_pass'] for r in rows),
        'output_mode':'rule/template Marketing, extractive-or-abstaining Support; no LLM calls',
        'ai_comparison':{'status':'not_exercised','reason':'No verified provider key/model run; configured key intentionally empty in this isolated profile.'},
        'warm_read':{'endpoint':'owned /finances','samples':100,'concurrency':4,
            'p50_ms':round(times[math.ceil(.5*len(times))-1],3),
            'p95_ms':round(times[math.ceil(.95*len(times))-1],3),
            'error_rate':0,'transport':'new local loopback HTTP connection per request; native test JWT and real Mongo'},
        'limitations':['Expected labels check arithmetic, contracts, ACL and abstention; not factual entailment or business intelligence.',
            'First new-business reads are not process-cold latency. Scenario duration includes polling and scheduling.',
            'No live market data, model comparison, model-loaded memory benchmark or AWS sizing is established.']}
