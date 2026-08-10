# Fix Vulnerabilities & Import Error

## Root Cause
- Backend has 2 critical + multiple high vulnerabilities (python-jose, transformers, requests, chromadb)
- Frontend has high vulnerabilities (react-router-dom) + axios downgraded
- `motor.motor_asyncio` import fails because VSCode uses root `CODSOFT/venv` which lacks motor

## Plan
- [x] Analyze codebase and identify root cause
- [x] Confirm plan with user

## Steps
- [x] Fix backend critical/high vulnerabilities in `requirements.txt`
- [x] Fix frontend vulnerabilities in `package.json` + regenerate lockfile
- [x] Install/upgrade dependencies in correct venv to resolve motor import
- [x] Verify no vulnerabilities remain (pip-audit, npm audit)
- [x] Run backend tests (pytest) to verify no regressions
- [x] Verify frontend builds (npm run build)

## Completed Changes

### Backend (`backend/requirements.txt`)
- `python-jose[cryptography]` 3.3.0 → 3.5.0 (critical)
- `requests` 2.31.0 → 2.33.0 (high)
- `pytest` 7.4.3 → 9.0.3 (high)
- `pytest-asyncio` 0.21.1 → 1.4.0 (compatibility with pytest 9)
- `black` 23.12.0 → 26.3.1 (high)
- `python-dotenv` 1.0.0 → 1.2.2
- `transformers` → `>=5.3.0` (critical RCE PYSEC-2026-2289)

### Frontend (`frontend/package.json`)
- `react-router-dom` → 7.18.2 (high)
- `axios` → ^1.19.0
- `vite` → ^6.4.3 (moderate esbuild fix)
- `@vitejs/plugin-react` → ^4.7.0 (vite 6 compatible)
- Regenerated `package-lock.json` → `npm audit` reports **0 vulnerabilities**

### VSCode Import Resolution
- Created `.vscode/settings.json` pointing Python interpreter to `backend/venv` so VSCode resolves `motor.motor_asyncio`

## Verification
- Backend: `78 passed` via `backend/venv/Scripts/python.exe -m pytest -q`
- Frontend: `npm run build` succeeds (dist created)
- `npm audit`: **found 0 vulnerabilities**
- Backend imports OK: motor, jose 3.5.0, requests 2.33.0, transformers 5.14.1

## Remaining Non-Exploitable Advisories (no fix available = latest versions)
`pip-audit` still reports 2 advisories, both at their latest available versions with **no patched release**:

1. **chromadb 1.5.9** (PYSEC-2026-311) — NOT exploitable in this app. The app uses `chromadb.PersistentClient` (local doc store / query only, see `backend/app/rag/store.py`). The advisory targets the Chroma **HTTP server** endpoint with `trust_remote_code=true`, which this codebase never exposes.

2. **ecdsa 0.19.2** (PYSEC-2026-1325) — NOT exploitable in this app. It is a transitive dependency of `python-jose`, and the app signs JWTs with **HS256 (HMAC)** only (`backend/app/core/security.py`), never ECDSA. No newer ecdsa release exists (0.19.2 is the latest).
