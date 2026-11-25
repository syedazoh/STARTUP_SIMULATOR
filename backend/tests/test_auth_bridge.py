"""The bridge verifies identity and keeps existing ownership/role boundaries."""
from uuid import uuid4
from tests.test_businesses import client, _register_and_login, _auth_headers
from app.services import supabase_auth


def test_verified_bridge_requires_explicit_link_and_preserves_original_business(client,monkeypatch):
    email='bridge-owner@example.com'
    native=_auth_headers(_register_and_login(client,email))
    company=client.post('/api/businesses',headers=native,json={'company_name':'Original company','industry':'Software'}).json()
    subject=str(uuid4())
    async def verify(token):return subject,email
    monkeypatch.setattr(supabase_auth,'verify_identity',verify)
    headers={'Authorization':'Bearer fixture-verified-provider-session','X-Auth-Provider':'supabase','X-Requested-With':'XMLHttpRequest'}
    assert client.post('/api/auth/supabase-session',headers=headers).status_code==409
    assert client.post('/api/auth/link-supabase',headers=native,json={'access_token':'fixture-verified-provider-session'}).status_code==200
    assert client.post('/api/auth/supabase-session',headers={**headers,'Origin':'https://other.example'}).status_code==403
    assert client.post('/api/auth/supabase-session',headers={k:v for k,v in headers.items() if k!='X-Requested-With'}).status_code==403
    assert client.post('/api/auth/supabase-session',headers={**native,'X-Requested-With':'XMLHttpRequest'}).status_code==403
    response=client.post('/api/auth/supabase-session',headers=headers)
    assert response.status_code==200,response.text
    cookie_headers=response.headers.get_list('set-cookie')
    assert any('Path=/' in value and 'HttpOnly' in value and 'Max-Age=0' not in value for value in cookie_headers)
    assert any('Path=/api/auth' in value and 'Max-Age=0' in value for value in cookie_headers)
    bridged=_auth_headers(response.json()['access_token'])
    companies=client.get('/api/businesses',headers=bridged).json()
    assert [c['id'] for c in companies]==[company['id']]
    refresh=client.post('/api/auth/refresh',headers={'X-Requested-With':'XMLHttpRequest'})
    assert refresh.status_code==200
    assert client.post('/api/auth/logout',headers={'X-Requested-With':'XMLHttpRequest'}).status_code==204
    assert client.get('/api/businesses',headers=bridged).status_code==401
