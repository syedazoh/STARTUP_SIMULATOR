"""Owner-reported workforce context; never hires or changes approvals."""
import pytest
from pydantic import ValidationError
from app.models.business_schemas import BusinessCreate, Workforce
from tests.test_businesses import client, _register_and_login, _auth_headers

TEAM = {"total_headcount": 7, "positions": [
    {"department": "Engineering", "role": "Engineer", "count": 5, "employment_type": "full_time"},
    {"department": "HR", "role": "Coordinator", "count": 1, "employment_type": "part_time"},
]}

@pytest.mark.parametrize("value", [
    {**TEAM, "total_headcount": 2},
    {**TEAM, "positions": [{**TEAM['positions'][0], "count": 1.5}]},
    {**TEAM, "positions": [{**TEAM['positions'][0], "count": True}]},
    {**TEAM, "positions": [{**TEAM['positions'][0], "role": "  "}]},
    {**TEAM, "positions": [TEAM['positions'][0], TEAM['positions'][0]]},
])
def test_workforce_rejects_invalid_counts_and_duplicate_groups(value):
    with pytest.raises(ValidationError): Workforce.model_validate(value)

def test_team_matches_starting_headcount_on_creation():
    with pytest.raises(ValidationError):
        BusinessCreate(company_name='X', industry='X', starting_headcount=2, workforce=TEAM)
    assert BusinessCreate(company_name='X', industry='X').workforce is None

def test_workforce_roundtrip_and_tenant_boundary(client):
    owner = _auth_headers(_register_and_login(client, 'team-owner@example.com'))
    other = _auth_headers(_register_and_login(client, 'team-other@example.com'))
    created = client.post('/api/businesses', headers=owner, json={
        'company_name':'Team Co','industry':'Software','starting_headcount':7,'workforce':TEAM})
    assert created.status_code == 201, created.text
    business_id = created.json()['id']
    assert client.get(f'/api/businesses/{business_id}',headers=owner).json()['workforce']==TEAM
    changed = {'total_headcount':8,'positions':TEAM['positions']}
    assert client.put(f'/api/businesses/{business_id}/workforce',headers=other,json=changed).status_code==403
    assert client.put(f'/api/businesses/{business_id}/workforce',json=changed).status_code==401
    result = client.put(f'/api/businesses/{business_id}/workforce',headers=owner,json=changed)
    assert result.status_code==200, result.text
    assert result.json()['workforce']['total_headcount']==8
    assert result.json()['starting_headcount']==7 # context editing cannot silently hire
    assert client.get('/api/businesses',headers=other).json()==[]
    assert client.put(f'/api/businesses/{business_id}/workforce',headers=owner,json={**TEAM,'total_headcount':1}).status_code==422
