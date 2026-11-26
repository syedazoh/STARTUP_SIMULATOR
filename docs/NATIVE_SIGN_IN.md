# Current sign-in: original simulator account

Supabase sign-in is turned off for this release at the owner's request. No OTP email, Supabase configuration, confirmation callback or account-link form is needed. The retained provider integration is dormant; backend `SUPABASE_AUTH_ENABLED` defaults to false. Existing Supabase settings/accounts and MongoDB records are not deleted or migrated.

## Run locally

Keep the original MongoDB connection **and database name** in `backend/.env`. Start your existing Mongo service or allow your IP in your existing Atlas cluster. From the repository root in Windows Git Bash:

```bash
source .venv/Scripts/activate
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal from the root:

```bash
cd web
npm ci
npm run dev
```

Open **http://localhost:3000/login**, enter the email and password of your original Startup Simulator account. This is the account in MongoDB, not the password held only by Supabase. Keep `BACKEND_URL=http://127.0.0.1:8000` in `web/.env.local`. Restart both servers after pulling this change; hard refresh the page. No Supabase keys or emailed code are required. Existing native sessions may ask you to sign in once again.

If you only ever created a Supabase identity and never set a native simulator password, it cannot be copied or guessed: that case requires deliberate account recovery. Do not register a duplicate or change database names to recover an old business. This change does not reset any password, transfer ownership or claim to verify the owner's private database.

## Behavior

The Next form calls the existing FastAPI `/api/auth/login`. FastAPI verifies the stored password and issues the existing revocable native session. Next keeps the access and refresh credentials in HttpOnly cookies, forwards only the native bearer to protected APIs, and verifies/restores the session through native `/me` and `/refresh`. Ownership and role checks remain backend-authoritative. No anonymous access or fake authenticated user is introduced. Protected links return to the requested workspace after sign-in.

New-user registration is separate and creates a native Mongo account, then returns to sign-in. Incorrect credentials, duplicates, backend outages and throttling have clear errors. Logout revokes the native backend session and clears browser auth cookies while retaining appearance preferences.

Optional classic frontend: run `npm ci` and `npm run dev` in `frontend/`, then open localhost:5173. Its login redirects to Next. On the same hostname, it restores the same native identity without a second password or any Supabase identity mapping. Keep Next running when using classic. Native API refresh/logout retain existing Origin/custom-header guards; the cross-app restoration still permits only configured CLASSIC_APP_URL.

## Verification

Focused backend auth/provider tests use disposable Mongo and provider mocks; retained provider validation tests explicitly opt in, and a regression proves disabled provider auth never contacts the network. The production Next/browser journey uses real native FastAPI routes with disposable mongomock, no private account or external provider. Historical Supabase-code browser scripts document the previous flow and are superseded by `web/tests/native-login.browser.cjs` for the current entry. No deployment or live database recovery is implied.

Current local evidence: 28 backend auth/provider tests, 42 Next unit tests, 73 classic unit tests, lint/build and native-browser login/refresh/logout/registration passed. The saved workspace, seven-role and automation browser acceptance flows also passed with explicit native fixture users. Zero provider OTP/verification/refresh requests were recorded in the native-login journey. These are fixture-backed checks, not access to your private database or password.
