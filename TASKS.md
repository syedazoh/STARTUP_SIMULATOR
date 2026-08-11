# Tasks & Change Log

> **Operational note:** the `frontend` service's `node_modules` lives in an
> anonymous Docker volume (see the 2026-08-10 "Full docker compose up stack"
> entry below) so the host's `node_modules` doesn't shadow it. That volume
> **persists across normal recreates**, so after changing
> `frontend/package.json` or `package-lock.json`, a plain
> `docker compose up -d --build` will rebuild the image correctly but the
> *running* container may keep serving the old, stale `node_modules`. Force a
> fresh one with:
> `docker compose up -d --build --force-recreate --renew-anon-volumes frontend`

Running log of updates, planning decisions, and changes made to this project,
with the reasoning behind each one. Newest entries at the top.

Format for each entry:

```
## YYYY-MM-DD — Short title

**What changed:** ...
**Why:** ...
**Files touched:** ...
```

---

## 2026-08-10 — Full `docker compose up` stack working end-to-end (mongo + backend + frontend + test)

**What changed:**
- Switched `frontend/Dockerfile` and `frontend/Dockerfile.prod` build stage from
  `node:18-alpine` to `node:18-slim`, and both now run
  `npm install --no-save @rollup/rollup-linux-x64-gnu` right after the main
  `npm install`.
- Added an anonymous volume in `docker/docker-compose.yml`'s `frontend`
  service: `- /app/node_modules`, layered after the existing
  `../frontend:/app` bind mount.
- Verified end-to-end: `docker compose up -d` in `docker/` brings up
  `mongo` (27017), `backend` (8000, `/docs` → 200), and `frontend` (5173,
  Vite dev server → 200); `docker compose --profile test run --rm test`
  runs all 78 backend tests, all passing.

**Why:** Even after the earlier TLS/CA and `npm ci`→`npm install` fixes, the
frontend container kept crash-looping with
`Cannot find module '@rollup/rollup-linux-x64-{musl,gnu}'`. Root-caused in two
layers:
1. **npm bug** (upstream, [npm/cli#4828](https://github.com/npm/cli/issues/4828)):
   npm intermittently lists rollup's platform-specific native binary in
   `package-lock.json` but doesn't actually install it. Verified via isolated
   throwaway builds — happened on both `node:18-alpine` (musl) and
   `node:18-slim` (glibc), so it isn't an Alpine/musl-only issue. Fixed by
   force-installing that one package explicitly after the main install,
   which preserves full lockfile-pinned reproducibility for every other
   package (rejected the alternative of dropping `package-lock.json`
   entirely for the frontend build, which would make every build resolve
   against "latest matching" instead of a pinned, reviewable lockfile).
2. **The actual reason nothing I changed in the Dockerfile ever took
   effect**: `docker-compose.yml`'s frontend service bind-mounts
   `../frontend:/app` for live-reload during dev. That mount overwrites the
   *entire* `/app` directory — including the `node_modules` the image just
   built correctly — with whatever's on the host at `frontend/node_modules`.
   On this Windows dev machine that's a Windows-targeted `node_modules` with
   no Linux native binaries at all, so the container always ran with a
   broken `node_modules` regardless of what the image build produced. The
   standard fix is an anonymous volume (`/app/node_modules`) that shadows
   just that one subpath, so the container keeps its own image-built
   `node_modules` while the rest of the source still live-reloads from the
   host.

**Files touched:** `frontend/Dockerfile`, `frontend/Dockerfile.prod`,
`docker/docker-compose.yml`

---

## 2026-08-10 — Fixed multi-hour backend build stall (CUDA torch wheel)

**What changed:** `backend/Dockerfile` now installs `torch` from
`https://download.pytorch.org/whl/cpu` before `pip install -r requirements.txt`.

**Why:** After the TLS/CA fix below resolved `CERTIFICATE_VERIFY_FAILED`, the
backend build still failed — this time after ~7 hours, with a
`ReadTimeoutError` from `files.pythonhosted.org`. Cause: `sentence-transformers`
pulls in `torch`, and the default PyPI Linux wheel bundles CUDA runtime
dependencies (~2GB+), which is both large and unnecessary (the app only needs
CPU inference). Installing the CPU-only build first (a few hundred MB) avoids
downloading the CUDA variant entirely. Confirmed the local Windows venv
already resolved to a `+cpu` build for the same reason (Windows PyPI wheels
don't bundle CUDA the way Linux ones do), which is why this only showed up
once building inside the Linux container.

**Files touched:** `backend/Dockerfile`

---

## 2026-08-09 — Added Docker `test` service + fixed TLS interception in local builds

**What changed:**
- Added a `test` service to `docker/docker-compose.yml` (behind a `test` Compose
  profile) that builds the backend image and runs `python -m pytest -q`. Tests
  mock Mongo via `mongomock_motor`, so this service has no dependency on the
  `mongo` service.
- Added an optional local CA-trust mechanism to `backend/Dockerfile` and
  `frontend/Dockerfile`: both now `COPY docker-ca/extra-ca.crt*` (glob matches
  the always-present, empty, git-tracked `extra-ca.crt.example` by default) and
  install it into the image's trust store if non-empty.
- Added `backend/docker-ca/extra-ca.crt.example` and
  `frontend/docker-ca/extra-ca.crt.example` (empty placeholders, tracked in
  git) and gitignored the real `extra-ca.crt` siblings.
- Created `docker/.env` (gitignored) populated from `backend/.env` so
  `docker compose` has `GROQ_API_KEY`/`GROQ_MODEL` without hardcoding secrets
  into a tracked file.

**Why:** The user wants one command (`docker compose up`) to bring up every
container the project needs (Mongo, backend API, frontend) plus an on-demand
way to run the test suite in a container. While building the stack, the
backend/frontend image builds failed with
`SSL: CERTIFICATE_VERIFY_FAILED` when reaching PyPI/npm/Alpine's package CDN.
Root cause: Avast Antivirus performs HTTPS/TLS inspection (MITM) on this
Windows machine and injects its own root CA into the Windows trust store —
which the host trusts, but Docker containers (their own minimal CA bundles)
do not. Baking Avast's root CA directly into the committed Dockerfiles would
silently trust a personal antivirus's MITM cert in CI/EC2 builds where it's
irrelevant, so the fix is opt-in and machine-local: an empty placeholder is
committed, and each affected developer fills in their own
`docker-ca/extra-ca.crt` locally (never committed).

**Files touched:**
`docker/docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`,
`backend/docker-ca/extra-ca.crt.example`,
`frontend/docker-ca/extra-ca.crt.example`, `.gitignore`, `docker/.env` (local,
gitignored)

---

## 2026-08-09 — Started local MongoDB via Docker

**What changed:** Started Docker Desktop's engine and ran the existing
`mongo` Docker container (already present, previously exited) mapped to
`localhost:27017`, matching `backend/.env`'s `MONGODB_URL`.

**Why:** `backend/app/database/mongodb.py` already has a designed fallback:
if MongoDB isn't reachable within 2s, it transparently switches to an
in-memory store so the app still runs, but nothing persists across restarts.
No MongoDB service/container was running, so every request was silently
hitting the fallback. Confirmed the fix by calling `connect_to_mongo()` and
`ping_mongo()` directly — both now report a real Mongo connection.

**Files touched:** none (infra-only; superseded by the `docker/docker-compose.yml`
`mongo` service above going forward)
