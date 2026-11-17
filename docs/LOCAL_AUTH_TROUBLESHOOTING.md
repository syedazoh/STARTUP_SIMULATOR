# Local sign-in troubleshooting

`[vite] http proxy error: /api/auth/refresh` with `ECONNREFUSED` means the Vite process could not connect to FastAPI. It is not an invalid-password response and does not establish a Next.js authentication failure. In this reported case the owner confirmed FastAPI had not been started.

## Start the services

With the project's Python virtual environment active, from the repository root:

```bash
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Keep that terminal open. Open `http://127.0.0.1:8000/health`. For existing durable accounts, Mongo must be connected; restore/start the configured database rather than deleting it or recreating accounts. If uvicorn exits, resolve its actual startup error before retrying the frontend.

In another terminal, use **one of these frontends**:

- Next.js: `cd web`, `npm run dev`, open `http://localhost:3000`.
- Classic Vite: `cd frontend`, `npm run dev`, open `http://localhost:5173`.

Vite proxies `/api` to `API_PROXY_TARGET`, default `http://127.0.0.1:8000`. Docker uses its configured backend service hostname instead. Keep `frontend/.env` overrides consistent with the actual backend location. Connection failures now return an actionable HTTP 503 JSON response; no session is granted. The IPv4 default avoids local hostname/IPv6 ambiguity but cannot start a missing backend.

## Next.js / Supabase configuration

Next sign-in uses Supabase, then sends its bearer session to FastAPI for local ownership/role checks. It does not call the classic `/api/auth/refresh` route.

Set `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` in `web/.env.local`, and matching-project `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` in `backend/.env`. `BACKEND_URL=http://127.0.0.1:8000` is server-only. Use publishable/anon keys here, never service-role secrets in browser variables. Do not overwrite existing .env files or paste secrets into chat.

Set `APP_URL` to the origin used by the browser and configure the corresponding Supabase site/redirect URLs for `/auth/callback` or the documented email-confirmation route. Use one consistent localhost/127.0.0.1 origin. A phone on the LAN needs a reachable origin, not the phone's own localhost. Restart services after environment changes.

Register/confirm an account in that Supabase project. A pre-existing classic account is not automatically copied into Supabase. Use the same verified email, then explicitly link the original password from the workspace; never replace the old account/database to fix sign-in. Existing businesses remain owned by their original local user.

When Supabase requires email confirmation, signup sends the visitor to the confirmation notice. If the configured provider returns a valid session immediately, signup now continues to the workspace instead of incorrectly requiring verification. Missing/placeholder configuration is explained on auth pages before credentials are submitted. Network/provider errors, invalid credentials, confirmation and rate limits remain separate, with no raw provider error echoed.

## Read-only setup checker

From the repository root:

```bash
python scripts/check_local_auth.py --ui classic
python scripts/check_local_auth.py --ui next
```

The checker inspects local environment presence/project matching and FastAPI health. It prints no secret values, makes no login request and changes no account/configuration. A successful configuration check is not proof of live Supabase sign-in. Verify with your actual configured project after both services are running.

The disposable `scripts/studio-browser/check-auth.py` checks browser flows using the localhost identity fixture on port 8012, configured production Next on 3012 and a second Next instance with missing provider variables on 3013. It validates UI/cookie/control flow, not real email delivery or live provider setup.
