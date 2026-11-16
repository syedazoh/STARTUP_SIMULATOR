# Next.js command center — November 16 implementation

This is an additive Next.js workspace migration. Existing Vite screens and accounts remain available. It does not claim that the whole November 30 submission plan is complete.

## Local run (Windows Git Bash)
From the project root, update with `git pull origin main`. Keep your existing backend/.env and web/.env.local; do not overwrite them.

Terminal 1:
```bash
source .venv/Scripts/activate
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
If your environment is inside backend rather than the root, activate backend/.venv/Scripts/activate instead. Use the project's installed requirements; CI uses Python 3.11. Check http://127.0.0.1:8000/health says mongo connected before persistence acceptance. A healthy HTTP response from an in-memory fallback does not establish persistence.

Terminal 2, from the project root:
```bash
cd web
npm ci
npm run dev
```
Open http://localhost:3000/workspace. Sign in using your existing app email/password. Select a business name to open its command center. The separate Vite app is no longer required for these migrated features.

## Implemented path
- Create a business with starting budget, customers, headcount and resources; all five departments enabled. Backend derives owner identity.
- Read independent panels for finances, agent state, tasks, CEO plans and department reports. One failed panel does not replace other saved data with fabricated success.
- Select Finance, Marketing, HR or Operations and propose bounded simulated work through existing action services.
- Generate an AI CEO draft, review all typed assignments/costs and explicitly confirm activation. Existing automatic policies can execute eligible simulated assignments during activation; otherwise work waits in the shared approval pipeline.
- Inspect task origin/source, department, parent plan, proposal payload, CEO authorization, success criteria, status and recorded result. Current task API does not store a general deadline; UI says so instead of inventing one.
- Review and approve/reject internal simulation tasks. Approval executes immediately under the existing backend pipeline; an execution may still fail or be denied. Instagram/media actions are not decidable from this UI.
- Approval/rejection from this workspace includes a proposal fingerprint. Changed payload/status/asset/objective/revision is a 409; material fields are compared again in the atomic decision write. Legacy clients that omit the field remain compatible. This is not the full immutable task-version/outbox migration.
- Optional 15-second refresh while visible; manual refresh always available. This is HTTP refresh, not Socket.IO. Writes are never automatically retried.
- Open the existing Dataset launch laboratory for synthetic JSON/CSV preview/import, deterministic five-department review, owner approval, recorded outcomes and isolated reset.

## Acceptance on your laptop
1. Open the original business and confirm saved data remains visible.
2. Create a separate test business. Select Finance, propose a small allocation, review the exact payload and approve. Inspect result/status/report and refresh.
3. Generate a CEO plan using your configured provider, inspect its assignments, activate and confirm tasks appear under each department. If AI is unavailable, the UI must display an error rather than an invented plan.
4. Sign into a second app account. The original business must be absent; directly opening its command-center URL must deny access.
5. Restart the backend and confirm original IDs/tasks/reports remain on Atlas. A browser refresh against a disposable in-memory fixture is not this restart test.

## Repeatable automated checks
`cd web && npm test && npm run typecheck && npm run build`.
Backend: `cd backend && python -m pytest tests/test_workspace_tasks.py tests/test_tasks.py tests/test_execution_supervision.py tests/test_demo_api.py`.

CI's `workspace-browser` job starts `backend/tests/workspace_browser_fixture.py` only when SIMULATOR_BROWSER_TEST=1. It runs production Next.js against disposable identity, Mongo and model doubles. It tests business creation, Finance proposal/approval, CEO delegation, reload, responsive overflow and second-user isolation. Fixture functions are not imported by app.main and cannot access provider accounts. It is not a real Supabase/Atlas acceptance test. Browser screenshots/logs are attached to the CI run; no real tokens or account passwords are used.

## Still separate work
Durable workers/Redis, deadline scheduling, runtime immutable task versions for all action types, MCP service, improved document RAG, email/calendar integration, full Vite feature migration, staging/production deployment, backup/restore and evaluation/report submission. No external integration or deployment was performed by this slice.
