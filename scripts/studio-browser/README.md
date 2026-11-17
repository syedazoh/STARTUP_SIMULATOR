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

Covers production Next.js login, real WebGL, avatar selection, team-list fallback, synthetic preview, a newly persisted CEO → Finance budget delegation, exact-action approval, owner handoff, no replay after reload, 320–1600px overflow checks, 320/390px label collision through orbit, immersive/follow/Escape and reduced-motion cleanup. The reduced-motion canvas image must return byte-identically to the pre-preview image after exit. Captures go to ignored `.impeccable/review/`. This is not a live Supabase/Mongo or provider acceptance test.
