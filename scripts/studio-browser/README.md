# Disposable studio browser acceptance

These scripts use only a **localhost fake identity/API service and synthetic records**. They do not open the project database or call external providers. Never deploy the fixture. Start a fresh fixture process for each check because the synthetic approval changes its in-memory task.

Prerequisites: the existing backend Python dependencies (`fastapi`, `uvicorn`), development-only `playwright` and its Chromium browser. Run `python -m playwright install chromium` after installing Playwright in your development environment. The browser is headless. `STUDIO_CHROMIUM_PATH` optionally selects an installed Chromium binary; without it, Playwright uses its installed browser.

From the repository root, terminal one:

```bash
python scripts/studio-browser/fixture.py
```

Terminal two, **test configuration only** (Git Bash/Linux):

```bash
cd web
npm ci
npm run build
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:8012 NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=fixture-only BACKEND_URL=http://127.0.0.1:8012 APP_URL=http://localhost:3012 npm run start -- --port 3012
```

Terminal three:

```bash
python scripts/studio-browser/check.py
```

Covers production Next.js login, real WebGL, avatar selection, team-list fallback, synthetic preview, a newly persisted CEO → Finance budget delegation, all five queued explicit agent handoffs in one event snapshot, HR → Operations preview and participant-role labels, exact-action approval, owner handoff, no replay after reload, 320–1600px overflow checks, 320/390px label collision through orbit, immersive/follow/Escape and reduced-motion cleanup. The reduced-motion canvas image must return byte-identically to the pre-preview image after exit. Captures go to ignored `.impeccable/review/`. This is not a live Supabase/Mongo or provider acceptance test.

Agent-focus checks also cover decision-log-only HR → Finance coordination, one visible avatar under the HR filter and all five after All events. For Vite, run `API_PROXY_TARGET=http://127.0.0.1:8012 npm run dev -- --host 127.0.0.1` from frontend with the fixture running, then `python scripts/studio-browser/check-vite.py` from the root. That check uses disposable browser-intercepted identity and verifies avatar filtering plus responsive dashboard/history/profile surfaces. It does not test live login or provider execution.

## Shared workflow/native auth acceptance
Run `SIMULATOR_FIXTURE_ONLY=1 PYTHONPATH=backend python scripts/studio-browser/shared_workflow_backend.py` from the root with backend/test dependencies installed. This disposable backend uses real application/native-auth/services with a mock database and explicitly mock model/image providers on :8013. Never deploy it. Build Next, then start it on :3025 with `BACKEND_URL=http://127.0.0.1:8013`. Run `node scripts/studio-browser/check-shared-workflow.mjs` (uses web's Playwright and `/usr/bin/chromium`). It creates only synthetic fixture accounts, never sends real emails, and checks all five roles, linked submissions/revision/approvals, two-role image preview/download/revision and voice/typed fallback with browser speech mocks. Output goes to `/tmp/workflow-browser`. This does not prove live inference, image quality, physical microphone behavior or persistent Mongo recovery.
