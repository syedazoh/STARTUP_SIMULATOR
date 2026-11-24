import asyncio
import csv
import io
import pytest
from app.services.exports import csv_text
from tests.test_account_isolation import accounts  # noqa: F401


def test_tenant_owned_downloads_allowlist_bound_and_csv_formula_protection(accounts):
    c, h, a, b = accounts
    db = c.app.state.db
    async def seed():
        for bid in [a, b]:
            await db['decision_logs'].insert_one({'business_id': bid, 'timestamp': '2026-11-24T00:00:00Z',
                'event_type': 'budget_request', 'source': '=HYPERLINK("x")', 'api_key': 'private-root',
                'data': {'task_id': 'test-task', 'access_token': 'private-nested',
                'result': {'status': 'executed', 'reasoning': '  +CMD()', 'financial_amount': 25,
                'refresh_token': 'private-result', 'credentials': {'password': 'private-deep'}}}})
            await db['collaboration_events'].insert_one({'business_id': bid, 'event_id': 'one',
                'timestamp': '2026-11-24T00:01:00Z', 'source': 'ceo', 'sender': 'ceo', 'receiver': 'finance',
                'data': {'title': '@SUM(1)', 'token': 'private-event'}})
    asyncio.run(seed())
    url = f'/api/businesses/{a}/evidence'
    assert c.get(url, headers=h['bob']).status_code == 403
    assert c.get(url).status_code == 401
    response = c.get(url, headers=h['alice'])
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'private, no-store'
    assert response.json()['truncated'] is False
    assert len(response.json()['records']) == 2
    assert all(r['business_id'] == a for r in response.json()['records'])
    assert 'private-' not in response.text and b not in response.text
    result = c.get(url+'?format=csv', headers=h['alice'])
    rows = list(csv.DictReader(io.StringIO(result.text)))
    assert rows[0]['reasoning'] == "'@SUM(1)"
    assert rows[1]['source'].startswith("'=") and rows[1]['reasoning'].startswith("'  +")
    assert c.get(url+'?limit=1', headers=h['alice']).json()['truncated'] is True
    assert c.get(url+'?limit=501', headers=h['alice']).status_code == 422
    assert len(c.get(url+'?kind=decision', headers=h['alice']).json()['records']) == 1
    assert c.get(url+'?kind=credentials', headers=h['alice']).status_code == 422


@pytest.mark.parametrize('value', ['=1+1', '+1', '-1', '@sum(1)', '\tcmd', '\rcmd', '\ncmd', '  =cmd'])
def test_all_spreadsheet_prefixes_are_protected(value):
    row = next(csv.DictReader(io.StringIO(csv_text({'records': [{'reasoning': value}]}))))
    assert row['reasoning'] == "'"+value
