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

## 2026-08-13 — Phase 7: RAG expansion to all five agents + Memory Inspector

**What changed:**
- Generalized `retrieve_memory`/`persist_memory` (previously Finance-only,
  see the 2026-08-09 Chroma entry further down) to Marketing, HR,
  Operations, and CEO. Each now retrieves a similar past decision before
  its LLM call and cites it via a new `precedent_cited` field (added to
  `MarketingDecision`, `HRDecision`, `OperationsDecision`,
  `ArbitrationDecision` — Finance already had it), then persists its own
  decision afterward — mirroring Finance's existing LangGraph shape
  (`check_policy` → policy-shortcut or `retrieve_memory` → `call_llm` → …
  → `persist_memory`). No new Chroma architecture needed: all five agents
  already shared one `DecisionMemoryStore` collection, filtered by
  `agent_id` (which already encodes `business_id`, e.g.
  `"finance_<business_id>"`), so this was purely wiring more callers into
  what existed.
- `DecisionMemoryStore.get_recent()` (new) — browses an agent's memories
  without a search query, for the inspector's default view; `query_similar`
  (existing) handles the free-text search case.
- New `GET /api/businesses/{id}/agents/{agent}/memory?query=&k=` — the read
  side, resolving the agent's real `agent_id` from the live registry rather
  than re-deriving the `"{agent}_{business_id}"` string convention in a
  second place.
- New `/memory-inspector` page (the spec's Part 1 described this as already
  existing in the frontend; the Phase 1 audit found it didn't — built fresh
  here): agent tabs, free-text search with distance scores, browse-recent
  when the search box is empty.

**Bug caught and fixed during implementation:** extending memory writes to
all five agents meant every test that directly instantiates
Marketing/HR/Operations/CEO and exercises a decision path — including the
*policy-shortcut* path, which (like Finance) still reaches `persist_memory`
even though it skips `retrieve_memory` — started hitting the real
`DecisionMemoryStore` unless mocked. Caught by noticing `chroma_data/chroma.sqlite3`'s
mtime changing after running `test_simulation.py`/`test_policies.py`/etc.
Fixed by extending each affected test file's existing
fake-memory-store-via-monkeypatch pattern (already established in
`test_simulation.py` for Finance) to cover the newly-wired agent modules
too, in `test_simulation.py`, `test_policies.py`, `test_agents.py`, and
`test_negotiation.py`.

**Why:** Part of the phased build plan (Phase 7 — RAG expansion). The spec
frames this as "a generalization of existing code, not new architecture,"
which held up in practice — the only real design decision was how the
inspector resolves an agent's `agent_id` (via the live registry, not by
re-implementing the naming convention).

**Verified:** 152/152 backend tests passing (14 new: `get_recent` coverage
plus one precedent-citation round-trip test per newly-wired agent in
`test_rag.py`, and 5 in `test_memory_routes.py` covering browse/search/
ownership/unknown-agent), frontend build clean, and the full flow driven
live in a browser: memory inspector empty on a fresh business → triggered
and approved a real Finance budget request (actual Groq decision) → memory
inspector showed the new entry under Finance → confirmed the Marketing tab
stayed empty (no cross-agent leakage) → free-text search returned the
entry with a real vector distance score. Zero console errors. (One
Playwright-only flake during verification — rapid-fire `page.goto()` calls
interrupted in-flight requests, not an app bug — resolved by adding small
settling waits between navigations in the test script.)

**Files touched:** `backend/app/rag/store.py`, `backend/app/agents/schemas.py`,
`backend/app/agents/marketing_agent.py`, `backend/app/agents/hr_agent.py`,
`backend/app/agents/operations_agent.py`, `backend/app/agents/ceo_agent.py`,
`backend/app/models/memory_schemas.py` (new),
`backend/app/api/routes/memory.py` (new), `backend/app/main.py`,
`backend/tests/test_rag.py`, `backend/tests/test_memory_routes.py` (new),
`backend/tests/test_simulation.py`, `backend/tests/test_policies.py`,
`backend/tests/test_agents.py`, `backend/tests/test_negotiation.py`,
`frontend/src/pages/MemoryInspector.jsx` (new), `frontend/src/App.jsx`,
`frontend/src/components/Layout.jsx`

---

## 2026-08-13 — Phase 6: admin interface (read-only aggregate views, no credential access)

**What changed:**
- New `GET /api/admin/businesses`, `GET /api/admin/businesses/{id}`,
  `GET /api/admin/system-health` — all gated by the `require_admin`
  dependency built in Phase 1. Data is aggregate operational metadata only
  (owner email, task status counts, decision counts, latest simulation
  status pulled from the existing `simulation_runs` collection, Mongo
  connectivity) — nothing invented that isn't backed by a real collection.
- No admin route imports `services/credentials.py`'s `get_decrypted_token`
  or queries the `credentials` collection — that's a property of what
  `routes/admin.py` was written to touch, not a permissions check a future
  route could bypass. Directly tested: connected a real credential with a
  distinctive secret token, then asserted it never appears in any admin
  response body, and that the admin module never imported the decrypt
  function at all (checked via the module's actual namespace, not a
  source-text grep, which would have false-positived on this very
  explanation in the module's own docstring).
- `scripts/promote_admin.py`: a CLI, not an API endpoint, promotes a user
  to admin by email. Deliberately no self-serve "become admin" route — that
  would be a real privilege-escalation hole. Mirrors the existing
  `scripts/run_simulation.py` convention.
- Frontend: `/admin` (overview: total businesses, active simulations,
  registered users, recently created businesses), `/admin/businesses`
  (table), `/admin/businesses/:id` (detail — with an explicit on-page note
  that no credential data is ever shown), `/admin/system-health`, all
  behind a new `AdminRoute` guard (role-gated, redirects non-admins home)
  and `AdminLayout`. A conditional "Admin →" link appears in the regular
  sidebar only for `role === "admin"` users.
- Also fixed a pre-existing gap while wiring this up: `fetchMe` (which
  populates `role` client-side) was defined in `authSlice.js` but never
  actually dispatched anywhere, so `state.auth.user` was always `null`.
  Now dispatched from `ProtectedRoute` so role is known as soon as the
  user is authenticated.

**Why:** Part of the phased build plan (Phase 6 — Admin interface). The
explicit test target called out in the spec — confirm no admin-reachable
code path can read `credentials` — was treated as a first-class
requirement, not an afterthought.

**Verified:** 141/141 backend tests passing (8 new in `tests/test_admin.py`),
frontend build clean, and the full flow driven live in a browser: a plain
owner confirmed to have no "Admin" link and to be bounced back to their own
dashboard on a direct `/admin` visit; a seeded admin (via the same
in-process-DB technique the test suite uses, since the in-memory Mongo
fallback doesn't share state across separate processes — `promote_admin.py`
needs a real shared MongoDB to work against a running server) walked
through overview → businesses table → business detail → system health,
confirming the owner's connected Instagram credential secret never
appeared anywhere on the admin pages. Zero console errors.

**Files touched:** `backend/app/models/admin_schemas.py` (new),
`backend/app/api/routes/admin.py` (new), `backend/scripts/promote_admin.py`
(new), `backend/app/main.py`, `backend/tests/test_admin.py` (new),
`frontend/src/components/AdminRoute.jsx` (new),
`frontend/src/components/AdminLayout.jsx` (new),
`frontend/src/pages/AdminOverview.jsx` (new),
`frontend/src/pages/AdminBusinesses.jsx` (new),
`frontend/src/pages/AdminBusinessDetail.jsx` (new),
`frontend/src/pages/AdminSystemHealth.jsx` (new),
`frontend/src/components/ProtectedRoute.jsx`, `frontend/src/components/Layout.jsx`,
`frontend/src/App.jsx`

---

## 2026-08-13 — Phase 5: per-agent chatbot, wired through the same task pipeline

**What changed:**
- New `chat_threads` collection (one thread per business+agent) and
  `GET`/`POST /api/businesses/{id}/agents/{agent}/chat` routes.
- `services/chat.py` builds a prompt from the agent's persona, the
  business's `business_profiles` document, the agent's **live status**
  (`budget_pool`, `customer_base`, etc. — see the grounding fix below), and
  recent conversation history, then asks the LLM for a `ChatReply`
  (`agents/schemas.py`): a conversational `reply`, plus optionally
  `action_requested`/`action_type`/`action_payload_json` if the owner's
  message asked for something concrete.
- The LLM only ever *requests* an action — `send_message()` is the only
  code that turns an approved-looking request into a real `create_task()`
  call, gated against a per-agent whitelist (`AGENT_ACTIONS`) mirroring the
  manual action endpoints, so chat can't invent an action_type nothing
  actually knows how to execute or reach across agents (HR asking for a
  Finance action is silently ignored, not executed). This keeps
  chat-originated actions on the exact same manual/auto/threshold pipeline
  as every other entry point — no bypass, as called for in the spec.
- CEO gets a chat panel too but no action whitelist entry — arbitration is
  system-triggered, consistent with it having no manual action endpoint or
  policy either.
- Frontend: a `ChatPanel` (message bubbles, send box) added to every agent
  detail page, including CEO's.

**Bug caught and fixed during verification:** the first live-browser pass
showed Finance confidently answering "$250,000" to "how much budget do we
have?" — a hallucination, since the prompt only included the (often empty)
`business_profiles` document, never the agent's actual `budget_pool`.
Fixed by fetching the live agent's `get_status()` via the existing
`agent_registry` and including it in the prompt; re-verified live and
Finance now correctly reports the real figure. Added a regression test
(`test_prompt_is_grounded_in_the_agents_live_status`) asserting the live
status appears in the prompt sent to the LLM.

**Why:** Part of the phased build plan (Phase 5 — Chatbot). The point of
routing chat actions through `create_task` rather than executing directly
was to avoid a second, ungated "the chatbot did it" code path alongside
the task queue built in Phase 2.

**Verified:** 133/133 backend tests passing (11 new in `tests/test_chat.py`,
mocking the LLM the same way `test_negotiation.py`/`test_policies.py`
already do for other agents' direct LLM calls), frontend build clean, and
the full flow driven live in a browser against the real Groq API: asked
Finance a factual question (correctly grounded answer), asked it to submit
a budget request (created a `pending_approval` task, visible in the
dashboard queue and in chat history after a page reload), and exercised
CEO's chat panel — zero console errors throughout.

**Files touched:** `backend/app/services/chat.py` (new),
`backend/app/models/chat_schemas.py` (new),
`backend/app/api/routes/chat.py` (new), `backend/app/agents/schemas.py`
(added `ChatReply`), `backend/app/models/documents.py` (added
`ChatThreadDocument`), `backend/app/main.py`,
`backend/tests/test_chat.py` (new),
`frontend/src/components/ChatPanel.jsx` (new),
`frontend/src/pages/AgentDetail.jsx`

---

## 2026-08-13 — Phase 4: media asset upload + agent review flow

**What changed:**
- New `media_assets` collection and `POST /api/tasks/{id}/assets` upload
  endpoint (multipart file + `media_type`), only reachable while a task is
  `awaiting_asset`.
- `services/media_assets.py` saves the upload to local disk under
  `backend/uploads/` (dev-only — swap for real object storage like S3
  before this handles real user uploads in prod, flagged in the module
  docstring) and runs an automated review pass. The review itself
  (`_review_asset`) is a deterministic stub standing in for a real
  brand-fit/vision model — Phase 4's job was the upload → review →
  task-transition wiring, not the review logic itself.
- Only an `approved` verdict clears the task into the normal
  `pending_approval` queue; `rejected`/`reshoot_requested` sends it back to
  `awaiting_asset` so the owner can re-upload.
- Marketing's `reel-request` action (`campaign_name` + `brief`) is the
  reference implementation: it's the first action created with
  `requires_asset=True`. Once approved it shares the same
  `post_to_instagram` tool `instagram_post` uses in `execute_task` — a reel
  is just a post with a required attachment, so `EXTERNAL_ACTION_HANDLERS`
  maps both action types to one handler rather than duplicating it.
- Frontend: the Task Queue's card swaps to an upload UI (media type +
  file picker) when a task is `awaiting_asset`, shows the review
  verdict/notes inline once submitted, and a new "Request a Reel" form
  sits on the Marketing agent page alongside the Phase 3 Instagram panels.

**Why:** Part of the phased build plan in the original spec doc (Phase 4 —
Media asset flow). Some agent actions (e.g. a promotional reel) can't
execute without a human supplying an asset first; this makes that a first-
class task state instead of a bespoke Marketing-only code path, so any
future agent/action needing an upload reuses the same `awaiting_asset` →
review → `pending_approval` transition.

**Verified:** 122/122 backend tests passing (7 new in
`tests/test_media_assets.py`), frontend build clean, and the full flow
driven live in a real browser (Playwright) — request a reel → task lands
awaiting an asset → upload an image → auto-approved and flips to normal
approve/reject controls → connect Instagram → approve → executes and
posts — zero console errors.

**Files touched:** `backend/app/models/media_asset_schemas.py` (new),
`backend/app/services/media_assets.py` (new), `backend/app/services/social.py`,
`backend/app/services/tasks.py`, `backend/app/models/documents.py`,
`backend/app/api/routes/tasks.py`, `backend/app/api/routes/agent_actions.py`,
`backend/requirements.txt` (added `python-multipart`), `.gitignore` (added
`backend/uploads/`), `backend/tests/test_media_assets.py` (new),
`frontend/src/components/AssetUploadCard.jsx` (new),
`frontend/src/components/ReelRequestForm.jsx` (new),
`frontend/src/components/TaskQueue.jsx`, `frontend/src/pages/AgentDetail.jsx`,
`frontend/src/store/slices/tasksSlice.js`

---

## 2026-08-12 — Phase 3: credential vault (envelope encryption) + mock Instagram connect

**What changed:**
- Envelope encryption scheme in `core/crypto.py`: one master key
  (`CREDENTIAL_MASTER_KEY`, env-injected — a fixed dev-only default ships
  in `config.py` so the app runs out of the box, but must be overridden
  before storing anything real) encrypts a per-user Fernet data key
  generated at registration and stored encrypted on the user document;
  each connected credential is then encrypted with its owning user's data
  key, not the master key directly.
- New `credentials` collection + business-scoped routes: `GET` (metadata
  only — provider, `connected_at`, `last_used_at`, scopes, never the
  secret), `POST /{provider}/connect`, `DELETE /{provider}`.
- `services/credentials.py` is the only place a credential is ever
  decrypted (`get_decrypted_token`), and it's not imported by any route —
  only by tool functions like the new `services/social.py::post_to_instagram`,
  which use the value for one outbound call and let it fall out of scope.
  No route or admin-facing code path can reach a plaintext token; that's a
  property of what this module exposes, not a permissions check a future
  route could bypass.
- `execute_task` gained an `EXTERNAL_ACTION_HANDLERS` registry so
  action_types with a real external side effect (currently
  `instagram_post`) route through a dedicated handler instead of the
  simulated-agent-decision path `budget_request` etc. still use.
- Connect flow is a **mock**: the owner pastes an access token (what a real
  OAuth redirect would eventually hand back) rather than driving an actual
  Meta OAuth dance — there's no registered Meta app to redirect to yet.
  Swapping in real OAuth later only touches `routes/credentials.py`.
- Added `delete_one` to the in-memory Mongo fallback (`database/mongodb.py`)
  since credential revoke needed it and the fallback didn't support it yet.
- Frontend: a "Connected Accounts" card (connect/disconnect, token input)
  and a "Post to Instagram" action form, both on the Marketing agent page.

**Why:** Part of the phased build plan (Phase 3 — Credential vault + first
live integration). Two decisions made with the user before starting:
(1) mock connect flow rather than real Meta OAuth, since no app
credentials exist yet; (2) master key from an env var for now rather than
AWS KMS, to keep local dev unblocked (swappable later since the encryption
service only cares where the key comes from, not how it's fetched).

**Verified:** 115/115 backend tests passing (11 new in
`tests/test_credentials.py`, including that connect/list responses never
contain the raw token anywhere in the response body), frontend build
clean, full connect → post-without-credential(fails cleanly) →
connect → post → approve → executes flow driven live in a browser with
zero console errors and confirmed no token ever appears in the DOM or
captured network log.

**Files touched:** `backend/app/core/crypto.py` (new),
`backend/app/services/credentials.py` (new), `backend/app/services/social.py`
(new), `backend/app/models/credential_schemas.py` (new),
`backend/app/api/routes/credentials.py` (new),
`backend/app/api/routes/auth.py`, `backend/app/api/routes/agent_actions.py`,
`backend/app/config.py`, `backend/app/database/mongodb.py`,
`backend/app/main.py`, `backend/app/models/documents.py`,
`backend/app/services/tasks.py`, `backend/requirements.txt` (added
`cryptography` as a direct dependency), `backend/.env.example`,
`backend/tests/test_credentials.py` (new),
`frontend/src/components/ConnectedAccounts.jsx` (new),
`frontend/src/components/InstagramPostForm.jsx` (new),
`frontend/src/pages/AgentDetail.jsx`

---

## 2026-08-12 — Phase 2: task/approval pipeline, wired end-to-end through Finance

**What changed:**
- New `tasks` and `agent_modes` collections plus one shared
  `create_task`/`execute_task` pipeline (`services/tasks.py`): manual mode
  (the default) queues every action as `pending_approval`; auto mode
  executes immediately only when the action's dominant scalar (e.g.
  budget-request `amount`) is within a configured threshold, otherwise it
  still falls back to the queue as a safety net.
- Kept `agent_modes` strictly separate from the pre-existing
  `agent_policies` threshold system (a decision made with the user before
  starting): `agent_policies` still only governs whether an agent's own
  LLM reasoning short-circuits; `agent_modes` is the new, orthogonal
  concept of whether the owner must approve before an action's effects
  apply at all.
- New routes: business-scoped task listing
  (`GET /api/businesses/{id}/tasks`), and task-id-addressed decisions
  (`POST /api/tasks/{id}/approve|reject|request-changes`) via a new
  `get_owned_task` dependency that resolves ownership from the task's
  `business_id` rather than a path param.
- Finance's budget-request endpoint is the reference implementation,
  wired end-to-end through `create_task`; Marketing/HR/Operations are
  unchanged and still execute directly (next in line for the same wiring,
  not intentionally skipped).
- Frontend: a Task Queue panel on the dashboard (approve / reject /
  request changes inline, polls every 3s) and a manual/auto Execution Mode
  toggle on each agent detail page, sitting alongside (not replacing) the
  existing Automation Policy form.

**Why:** Part of the phased build plan (Phase 2 — Task/approval pipeline).
Every agent action that should be reviewable needed one shared "check mode
→ maybe queue → maybe execute" code path instead of five bespoke ones per
agent.

**Verified:** 104/104 backend tests passing (15 new, 3 existing Finance
action tests updated to reflect manual-by-default now requiring an
explicit approve step), frontend build clean, full flow driven live in a
browser (register → onboard → trigger a manual budget request → see it
queued → approve → budget actually moves → switch to auto mode → a
request under threshold now executes immediately) with zero console
errors.

**Files touched:** `backend/app/services/tasks.py` (new),
`backend/app/models/task_schemas.py` (new),
`backend/app/models/agent_mode_schemas.py` (new),
`backend/app/api/routes/tasks.py` (new),
`backend/app/api/routes/agent_modes.py` (new),
`backend/app/api/deps.py`, `backend/app/api/routes/agent_actions.py`,
`backend/app/main.py`, `backend/app/models/documents.py`,
`backend/tests/test_tasks.py` (new), `backend/tests/test_agent_modes.py`
(new), `backend/tests/test_agent_actions.py`,
`frontend/src/store/slices/tasksSlice.js` (new),
`frontend/src/components/TaskQueue.jsx` (new),
`frontend/src/components/AgentModeForm.jsx` (new),
`frontend/src/components/AgentActionForm.jsx`, `frontend/src/pages/Dashboard.jsx`,
`frontend/src/pages/AgentDetail.jsx`, `frontend/src/store/index.js`

---

## 2026-08-12 — Phase 1: role system foundation + `business_profiles`

**What changed:**
- Added `role` to the `users` collection (defaults to `"owner"` on
  registration) and a server-side `require_admin` FastAPI dependency
  (`deps.py`) that reads role from the DB-backed user object, never a
  client-supplied value — laying the foundation for the admin surface
  planned in Phase 6.
- New `business_profiles` collection: one canonical
  brand/product/marketing/finance/operations document per business, plus
  an append-only `custom_context` list, structured so it can later be
  injected wholesale into agent prompts and re-embedded into that
  business's RAG collection (Phase 7).
- New routes: `GET`/`POST /api/businesses/{id}/profile` (full-document
  upsert) and `POST /api/businesses/{id}/profile/context` (appends a note
  without touching the rest of the profile).
- Onboarding wizard is now a two-step flow: the existing business-basics
  step, then a new business-context step (skippable) that writes the full
  profile shape.

**Why:** Kicked off the phased build plan for the target architecture
described in the project spec doc (role system, task pipeline, credential
vault, media assets, chatbot, admin surface, RAG expansion, hardening).
Phase 1 lays the two foundations later phases depend on: a role concept to
gate the future admin surface, and a real business-context object for
agents to draw from instead of just name/industry.

Before starting, audited the spec's "current state" claims against the
actual code: backend matched closely (one nuance — the CEO agent isn't
LangGraph-based, it calls Groq directly); the frontend turned out to be
Vite + React + react-router-dom (business-scoped routes like
`/b/:businessId/dashboard`), not Next.js as the spec assumed, and the
onboarding wizard was thinner than described (no agent-selection step, no
file upload) — corrections carried forward as working knowledge rather
than a separate doc.

**Verified:** 89/89 backend tests passing (7 new in
`tests/test_business_profiles.py`, plus role/`require_admin` coverage
added to `tests/test_auth.py`), frontend build clean, manual end-to-end
smoke test (register → login → create business → read/write profile →
append context).

**Files touched:** `backend/app/models/business_profile_schemas.py` (new),
`backend/app/api/routes/business_profiles.py` (new),
`backend/app/api/deps.py`, `backend/app/api/routes/auth.py`,
`backend/app/main.py`, `backend/app/models/auth_schemas.py`,
`backend/app/models/documents.py`, `backend/tests/test_auth.py`,
`backend/tests/test_business_profiles.py` (new),
`frontend/src/pages/Onboarding.jsx`,
`frontend/src/store/slices/businessProfileSlice.js` (new),
`frontend/src/store/index.js`

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
