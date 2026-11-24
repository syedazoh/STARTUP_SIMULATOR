"""Actual HTTP API + independent role processes + real Mongo. Disposable DB only."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from uuid import uuid4
import httpx
import pytest
from pymongo import MongoClient


def wait_until(check, seconds=25):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            result = check()
            if result:
                return result
        except (httpx.ConnectError, httpx.ReadTimeout):
            pass
        time.sleep(.1)
    raise AssertionError('Acceptance deadline expired')


def test_http_scenario_across_actual_role_processes_and_crash(tmp_path):
    uri = os.environ.get('MONGODB_INTEGRATION_URL')
    if not uri:
        pytest.skip('MONGODB_INTEGRATION_URL required; never uses the configured user database')
    root = Path(__file__).resolve().parents[2]
    name = 'distributed_test_' + uuid4().hex
    mongo = MongoClient(uri, serverSelectionTimeoutMS=5000)
    mongo.admin.command('ping')
    with socket.socket() as port_socket:
        port_socket.bind(('127.0.0.1', 0))
        port = port_socket.getsockname()[1]
    env = {**os.environ, 'PYTHONPATH': str(root), 'MONGODB_URL': uri,
        'MONGODB_DB_NAME': name, 'BACKGROUND_JOBS_ENABLED': 'True', 'DEBUG': 'True',
        'GROQ_API_KEY': '', 'RAG_DENSE_ENABLED': 'False', 'RAG_RERANKER_ENABLED': 'False',
        'CHROMA_PERSIST_DIR': str(tmp_path / 'chroma'), 'HF_HUB_OFFLINE': '1'}
    log = (tmp_path / 'api.log').open('w')
    api = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app',
        '--host', '127.0.0.1', '--port', str(port)], cwd=root, env=env, stdout=log, stderr=log)
    pids = []
    started = time.monotonic()
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{port}', timeout=30) as client:
            wait_until(lambda: client.get('/health').is_success)
            creds = {'email': 'distributed@example.com', 'password': 'Local-test-only-12345'}
            assert client.post('/api/auth/register', json=creds).status_code == 201
            token = client.post('/api/auth/login', json=creds).json()['access_token']
            client.headers['Authorization'] = 'Bearer ' + token
            business = client.post('/api/businesses', json={'company_name': 'Synthetic cross-process launch',
                'industry': 'Software', 'starting_budget': 1000}).json()['id']
            base = f'/api/businesses/{business}'
            run = client.post(base+'/distributed-runs', json={'idempotency_key': 'process-demo', 'seed': 17}).json()
            run_url = base+'/distributed-runs/'+run['run_id']
            # Crash immediately after a real role claim, before persisting a result.
            crash_code = """import asyncio,os
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.services.jobs import claim
async def crash():
 c=AsyncIOMotorClient(settings.mongodb_url)
 j=await claim(c[settings.mongodb_db_name], role='ceo')
 assert j and j['attempts']==1
 os._exit(17)
asyncio.run(crash())
"""
            crashed = subprocess.run([sys.executable, '-c', crash_code], cwd=root, env=env, timeout=25)
            assert crashed.returncode == 17
            row = mongo[name].background_jobs.find_one({'payload.role': 'ceo'})
            assert row['status'] == 'running' and row['result'] is None
            # Accelerate lease expiry rather than delaying the test for 180s.
            mongo[name].background_jobs.update_one({'_id': row['_id']}, {'$set': {'lease_until': 0}})
            for role in ('ceo', 'marketing', 'finance', 'hr', 'operations', 'support', 'strategy'):
                wait_until(lambda: mongo[name].background_jobs.find_one({'payload.role': role, 'status': 'queued'}) or (role == 'ceo' and row))
                process = subprocess.Popen([sys.executable, '-m', 'app.role_worker', '--role', role, '--once'],
                    cwd=root, env=env, stdout=subprocess.DEVNULL, stderr=log)
                pids.append(process.pid)
                assert process.wait(timeout=30) == 0
            view = wait_until(lambda: (r if (r := client.get(run_url).json())['status'] == 'ready_for_review' else None))
            assert [r['result']['worker_pid'] for r in view['roles']] == pids
            assert len(set(pids)) == 7 and api.pid not in pids
            assert view['roles'][0]['attempts'] == 2
            assert view['roles'][2]['result']['recommended_budget_minor'] == 10000
            assert view['roles'][5]['result']['mode'] == 'abstention'
            assert mongo[name].financial_accounts.count_documents({}) == 0
            task_response = client.post(run_url+'/proposal')
            assert task_response.status_code == 201, task_response.text
            task = task_response.json()
            assert task['status'] == 'pending_approval'
            assert client.post('/api/tasks/'+task['id']+'/approve', json={'expected_fingerprint': task['approval_fingerprint']}).json()['status'] == 'executed'
            report = client.get(run_url).json()
            assert report['task_status'] == 'executed' and report['recorded_outcome']
            account_before = mongo[name].financial_accounts.find_one({'_id': business})
            client.post(run_url+'/proposal')  # Replay cannot create a second task/effect.
            client.post('/api/tasks/'+task['id']+'/approve')
            assert mongo[name].tasks.count_documents({}) == 1
            account_after = mongo[name].financial_accounts.find_one({'_id': business})
            assert account_before == account_after
            evidence = {'synthetic': True, 'mode': 'rule_based', 'independent_worker_count': 7,
                'worker_pids': pids, 'api_pid': api.pid, 'ceo_attempts_after_crash': 2,
                'task_status': report['task_status'], 'duration_seconds': round(time.monotonic()-started, 3)}
            print('DISTRIBUTED_EVIDENCE '+json.dumps(evidence))
    finally:
        api.terminate()
        try:
            api.wait(timeout=10)
        except subprocess.TimeoutExpired:
            api.kill(); api.wait(timeout=5)
        log.close()
        mongo.drop_database(name)
        mongo.close()
