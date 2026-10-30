"""HTTP smoke test for an isolated local/CI Compose stack; never deploys anything."""
import argparse
import http.cookiejar
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('phase', choices=['before-restart', 'after-restart'])
parser.add_argument('--base-url', default='http://localhost:5173')
parser.add_argument('--state-file', required=True, type=Path)
args = parser.parse_args()
jar = http.cookiejar.CookieJar()
client = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(jar))


def request(path, method='GET', payload=None, token=None, refresh_cookie=None):
    headers = {'Origin': args.base_url.rstrip('/'), 'X-Requested-With': 'XMLHttpRequest'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if refresh_cookie:
        headers['Cookie'] = 'simulator_refresh=' + refresh_cookie
    body = json.dumps(payload).encode() if payload is not None else None
    if body is not None:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(args.base_url.rstrip('/') + path, data=body, headers=headers, method=method)
    try:
        response = client.open(req, timeout=30)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        text = response.read().decode()
        try:
            content = json.loads(text)
        except json.JSONDecodeError:
            content = text
        return response.status, content


for attempt in range(60):
    try:
        status, health = request('/api/health')
        if status == 200 and health['mongo'] == 'connected':
            break
    except (OSError, TypeError, KeyError):
        pass
    time.sleep(1)
else:
    raise RuntimeError('Frontend proxy/backend/MongoDB did not become ready')

if args.phase == 'before-restart':
    assert request('/')[0] == 200, 'Frontend HTML is unavailable'
    css_status, css = request('/src/index.css')
    assert css_status == 200 and '--tw-' in css, 'Tailwind stylesheet compilation failed'
    credentials = {'email': f'wiring-{secrets.token_hex(8)}@example.com', 'password': secrets.token_urlsafe(24)}
    assert request('/api/auth/register', 'POST', credentials)[0] == 201
    status, login = request('/api/auth/login', 'POST', credentials)
    assert status == 200
    token = login['access_token']
    assert request('/api/auth/me', token=token)[1]['email'] == credentials['email']
    status, business = request('/api/businesses', 'POST', {'company_name': 'CI wiring test', 'industry': 'Software'}, token)
    assert status == 201
    bid = business['id']
    status, task = request(f'/api/businesses/{bid}/agents/finance/actions/budget-request', 'POST', {'amount': 100}, token)
    assert status == 200 and task['status'] == 'pending_approval'
    status, executed = request(f"/api/tasks/{task['id']}/approve", 'POST', token=token)
    assert status == 200 and executed['status'] == 'executed'
    refresh = next(cookie.value for cookie in jar if cookie.name == 'simulator_refresh')
    args.state_file.write_text(json.dumps({**credentials, 'token': token, 'business_id': bid, 'refresh': refresh}))
    args.state_file.chmod(0o600)
    print('Real Compose: frontend, API proxy, MongoDB, registration/login, approval and persistence writes passed')
else:
    state = json.loads(args.state_file.read_text())
    token, bid = state['token'], state['business_id']
    assert request('/api/auth/me', token=token)[0] == 200, 'Session did not survive backend restart'
    status, businesses = request('/api/businesses', token=token)
    assert status == 200 and any(item['id'] == bid for item in businesses)
    status, finance = request(f'/api/businesses/{bid}/agents/finance', token=token)
    assert status == 200 and finance['budget_pool'] == 99900, 'Agent snapshot was not restored'
    status, refreshed = request('/api/auth/refresh', 'POST', refresh_cookie=state['refresh'])
    assert status == 200
    assert next(cookie.value for cookie in jar if cookie.name == 'simulator_refresh') != state['refresh']
    assert request('/api/auth/logout', 'POST', token=refreshed['access_token'])[0] == 204
    assert request('/api/auth/me', token=token)[0] == 401
    args.state_file.unlink()
    print('Real Compose: database/session/snapshot persistence across restart, refresh rotation and logout passed')
