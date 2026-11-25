# Local startup and existing-account recovery

Do not create a new Supabase project, Mongo database or company just to recover existing work. Keep your current `.env` files and the original MongoDB database. Never paste passwords, tokens or connection-string credentials into chat.

## What each service does

| Address | Service | Purpose |
| --- | --- | --- |
| http://localhost:3000 | Next.js (`web/`) | Supabase sign-in, company selector, command center, five department workspaces, boardroom, shared automation and datasets |
| http://localhost:5173 | Classic React/Vite (`frontend/`) | Retained agent pages with verified session restoration from Next; internal Marketing draft review |
| http://127.0.0.1:8000 | FastAPI (`backend/`) | Authenticated business actions, task approvals, workers and MongoDB access |
| Supabase project | Identity provider | Verifies the Next.js login; it does not replace the Mongo business database |
| MongoDB | Business database | Stores companies, original native accounts, tasks and other simulator records |

Both frontends belong to this repository and use the same backend. Sign in once through Next. The classic page restores a revocable native session through a verified same-host bridge; it does not ask for a second login. Original unlinked accounts still require explicit ownership linking. Do not copy tokens or assume a Supabase password is the original native password. See [same-screen code sign-in and exact settings](AUTH_ENTRY_2026_11_25.md).

## Check existing configuration

Open existing files in an editor. Preserve real values; the names below are not new keys to generate.

`web/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://YOUR_EXISTING_PROJECT.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=YOUR_EXISTING_PUBLISHABLE_KEY
BACKEND_URL=http://127.0.0.1:8000
APP_URL=http://localhost:3000
```

Use the URL and publishable/anon key from the **existing** Supabase project settings. Never put a service-role key in a `NEXT_PUBLIC_` variable. Keep Supabase site/redirect URLs consistent with `http://localhost:3000` and the configured callback routes.

`backend/.env`:

```env
SUPABASE_URL=https://YOUR_EXISTING_PROJECT.supabase.co
SUPABASE_PUBLISHABLE_KEY=YOUR_EXISTING_PUBLISHABLE_KEY
MONGODB_URL=YOUR_ORIGINAL_MONGO_CONNECTION_STRING
MONGODB_DB_NAME=YOUR_ORIGINAL_DATABASE_NAME
```

The Supabase URL must match the frontend project. The Mongo URL **and database name** must be the ones containing the original users/businesses. A new empty Mongo database can connect successfully and still show no old businesses. For an existing local Mongo installation, a URL may look like `mongodb://127.0.0.1:27017`; Atlas uses the connection string for the existing cluster. Preserve its credentials privately and allow your local connection as required by Atlas. Do not change databases blindly or enable volatile in-memory mode to recover persisted records.

## Start locally — Windows Git Bash

From the project root, terminal 1 (if the virtual environment is in the root):

```bash
source .venv/Scripts/activate
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If `.venv` is inside backend, activate that environment instead. Start your existing MongoDB service first when using local Mongo. Open http://127.0.0.1:8000/health and require `mongo: connected` before troubleshooting business records. Restart the backend after environment edits.

Terminal 2, from root:

```bash
cd web
npm ci
npm run dev
```

Open http://localhost:3000. Restart Next after environment changes; use the same browser origin consistently.

## Find and open your work

1. Sign in with the existing Supabase identity.
2. `/workspace` is the **company selector**, not the full company dashboard. If `auto_sim` or another existing company appears, open that company's Command center or one of its agent workspace links. Do not create a replacement company.
3. If your original company is missing, first confirm the original Mongo URL/database and the backend connection. Then use **Link existing account** with the original Startup Simulator email/password. This is a native-account credential check followed by a separately verified identity link; matching email alone is insufficient.
4. An invalid-original-credentials message means the original login was not accepted. An identity-verification error means check the matching Supabase project/session. A backend-unavailable error means check the backend/database. A conflict needs account-link resolution, not repeated company creation.
5. Successful linking preserves the existing ownership mapping; the application does not migrate or delete the original Mongo records in this UI change.

## Agent pages in Next

Company routes are business-scoped:

```text
/workspace/<business-id>/agents/ceo
/workspace/<business-id>/agents/finance
/workspace/<business-id>/agents/marketing
/workspace/<business-id>/agents/hr
/workspace/<business-id>/agents/operations
```

Each role page exposes its recorded tasks/state/history, an avatar, relevant simulation proposal form, saved chat, and shared automation/knowledge navigation. The four department roles expose their existing execution-mode and reasoning-policy settings; CEO exposes planning instead. An auto-mode change requires explicit acknowledgement. Chat may create proposals, and existing mode/policy can execute eligible simulated requests. Navigation and avatars do not authorize work.

Retained classic agent pages remain available as an optional third terminal. Marketing uses internal reviewable drafts; no social connection is needed:

```bash
cd frontend
npm ci
npm run dev
```

After signing in at localhost:3000, open http://localhost:5173 using the same hostname. Its verified bridge restores the same identity without a second login. Agent routes are `/b/<business-id>/agents/<role>`. Backend/provider permissions and setup still apply; access to a screen does not prove live email or social publishing is configured.


## Personalize and describe your team
Use **Appearance** at the top-right to choose Executive Glass, Pearl Water or Monolith, Emerald/Champagne/Lavender palette, color mode and decorative motion. Preferences stay in this browser; Reset appearance restores defaults.

Next: open your existing company’s Command center → **Team setup**. Classic: **Business Profile** → Team setup. For a new company, add departments/roles in the creation form. Unallocated employees remain “Not assigned yet”. These human staffing details are reported planning context, not a change to simulation HR headcount or permission to hire.
