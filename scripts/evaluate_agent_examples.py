"""Run authored examples through the real shared service in an isolated fixture DB.

Requires backend + test dependencies. Never uses the configured MongoDB. Reports
actual outputs for review; example answers are NOT sent to the model or auto-graded.
"""
import argparse
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', choices=['development', 'held_out', 'all'], default='development')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    # Prevent the fixture evaluator from starting workers or downloading models.
    os.environ['BACKGROUND_JOBS_ENABLED'] = 'false'
    os.environ['RAG_ALLOW_MODEL_DOWNLOAD'] = 'false'
    from unittest.mock import patch
    from fastapi.testclient import TestClient
    from mongomock_motor import AsyncMongoMockClient
    from app.main import app
    import app.database.mongodb as mongodb

    corpus = json.loads((ROOT / 'datasets/agent-conversations-v1/examples.json').read_text())
    cases = [c for c in corpus['examples'] if args.split == 'all' or c['split'] == args.split]
    results = []
    with patch.object(mongodb, 'AsyncIOMotorClient', lambda *a, **k: AsyncMongoMockClient()):
        with TestClient(app) as client:
            identities = {}
            for role in ['ceo','finance','marketing','operations','strategy']:
                email = f'evaluation-{role}@example.com'
                client.post('/api/auth/register', json={'email': email, 'password': 'isolated-fixture-password'})
                token = client.post('/api/auth/login', json={'email': email, 'password': 'isolated-fixture-password'}).json()['access_token']
                identities[role] = {'Authorization': f'Bearer {token}'}
            for case in cases:
                headers = identities[case['agent']]
                # Separate business per example prevents development/holdout leakage.
                business = client.post('/api/businesses', headers=headers, json={'company_name': 'Synthetic evaluation ' + case['id'], 'industry': 'Desk kits', 'starting_budget': 300}).json()['id']
                client.get(f'/api/businesses/{business}/finances', headers=headers)
                root = f'/api/businesses/{business}'
                outputs = []
                for message in case['conversation']:
                    if message['role'] != 'user':
                        continue
                    response = client.post(f'{root}/workflow/{case["agent"]}/turns', headers=headers, json={'request_id': str(uuid4()), 'content': message['content']})
                    outputs.append({'status': response.status_code, 'actual': response.json()})
                tasks = client.get(root + '/tasks', headers=headers).json()
                results.append({'id': case['id'], 'agent': case['agent'], 'split': case['split'], 'declared_scenario': case['scenario'], 'fixture': 'Isolated USD 300 business; no historical rows, deadlines, prior images or assigned submissions. Scenario-specific prerequisites beyond this fixture need manual setup/review.', 'outputs': outputs, 'conversation_created_no_tasks': tasks == [], 'human_review_checks': case['checks'], 'behavioral_score': None})
    sources = [o['actual'].get('source') for r in results for o in r['outputs']]
    report = {'synthetic_fixture': True, 'split': args.split, 'cases': len(results), 'model_status': 'model outputs recorded; human review required' if 'model' in sources else 'BLOCKED: no successful current-model responses; structured service/fallback outputs only', 'scoring': 'No accuracy claim. Expected answers were never passed into prompts. Several authored scenarios need additional setup; inspect fixture notes.', 'results': results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, default=str) + '\n')
    print(json.dumps({'cases': len(results), 'model_status': report['model_status'], 'output': str(args.output)}))


if __name__ == '__main__':
    main()
