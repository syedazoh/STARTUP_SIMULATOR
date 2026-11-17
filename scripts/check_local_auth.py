"""Check local auth wiring without printing or transmitting passwords/API keys."""
import argparse,json,os
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

def read_env(path):
    result={}
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            line=line.strip()
            if not line or line.startswith('#') or '=' not in line:continue
            key,value=line.removeprefix('export ').split('=',1)
            result[key.strip()]=value.strip().strip('"\'')
    return result

def configured(value):return bool(value and 'YOUR_' not in value.upper())

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ui',choices=['next','classic'],default='next')
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    backend={**read_env(root/'backend/.env'),**os.environ}
    web={**read_env(root/'web/.env'),**read_env(root/'web/.env.local'),**os.environ}
    classic={**read_env(root/'frontend/.env'),**read_env(root/'frontend/.env.local'),**os.environ}
    base=(web.get('BACKEND_URL') if args.ui=='next' else classic.get('API_PROXY_TARGET')) or 'http://127.0.0.1:8000'
    ok=True
    print('Selected frontend: '+('Next.js at http://localhost:3000 (web/)' if args.ui=='next' else 'Vite at http://localhost:5173 (frontend/)'))
    try:
        parsed=urlsplit(base)
        if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:raise ValueError()
        with urlopen(base.rstrip('/')+'/health',timeout=3) as response:health=json.load(response)
        if health.get('service')!='startup-simulator-backend':
            print('FAIL: the configured backend URL is not the FastAPI service.');ok=False
        else:
            print('OK: FastAPI is reachable.')
            if health.get('mongo')!='connected':
                print('FAIL: Mongo is unavailable. Existing persistent accounts require Mongo to be running.');ok=False
            else:print('OK: Mongo is connected.')
    except Exception:
        print('FAIL: cannot reach FastAPI /health. Start the backend on 127.0.0.1:8000 and check BACKEND_URL/API_PROXY_TARGET.');ok=False
    if args.ui=='next':
        for label,value in [('web Supabase URL',web.get('NEXT_PUBLIC_SUPABASE_URL')),('web publishable key',web.get('NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY')),('backend Supabase URL',backend.get('SUPABASE_URL')),('backend publishable key',backend.get('SUPABASE_PUBLISHABLE_KEY'))]:
            ready=configured(value);print(('OK: ' if ready else 'FAIL: ')+label+(' is set.' if ready else ' is missing or still a placeholder.'));ok=ok and ready
        a=web.get('NEXT_PUBLIC_SUPABASE_URL','').rstrip('/').lower();b=backend.get('SUPABASE_URL','').rstrip('/').lower()
        if a and b and a!=b:print('FAIL: web and backend Supabase project URLs differ.');ok=False
        print('Provider sign-in and email confirmation must still be verified with your real project; no login request was made.')
    print('Restart the affected services after changing .env files. No configuration values or secrets were printed.')
    return 0 if ok else 1

if __name__=='__main__':raise SystemExit(main())
