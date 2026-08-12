# Autonomous Startup Simulator — Complete Project Blueprint

This is the single, standalone execution spec for the entire project — frontend, backend, and database — combining what already exists in the repo with everything planned. Read this top to bottom before writing code; it's meant to be handed to Claude Code as the full build target.

---

## 1. What This Product Is

A multi-tenant web app where a business owner creates a virtual startup, and five autonomous LLM-backed agents (CEO/Strategy, Marketing, Finance, Operations, HR) run it forward through simulated time — reacting to market events, coordinating with each other, and either acting on their own or asking the owner for approval, depending on the mode the owner sets per agent. A separate admin surface lets the platform operator see registered businesses and system health without ever being able to see a business's private credentials or data.

---

## 2. System Architecture Overview

```
┌─────────────────┐      ┌──────────────────────────────┐      ┌─────────────┐
│   Next.js UI     │◄────►│         FastAPI backend        │◄────►│  MongoDB    │
│  (Owner + Admin) │  WS  │  (auth, agents, orchestration) │      │ (documents) │
└─────────────────┘      └──────────────┬───────────────┘      └─────────────┘
                                          │
                          ┌───────────────┼────────────────┐
                          ▼               ▼                ▼
                    LangGraph agents  ChromaDB (RAG)   Groq (Llama-3 LLM)
                          │
                          ▼
                 Event Bus (per business, pub/sub)
                          │
                          ▼
              Third-party APIs (Instagram, website CMS)
              — only ever called from execute_task(),
                credentials decrypted just-in-time
```

Everything routes through one event bus and one task/approval pipeline (defined below) so the five agents share infrastructure instead of each having bespoke plumbing.

---

## 3. Database Layer (MongoDB) — Full Schema

| Collection | Purpose |
|---|---|
| `users` | `{ _id, email, password_hash, role: "owner"\|"admin", data_key_encrypted, created_at }` |
| `businesses` | `{ _id, owner_user_id, name, industry, seed_capital, enabled_agents: [], status, created_at }` |
| `business_profiles` | One canonical JSON doc per business — brand, product, marketing, finance, operations, `custom_context`. This is what gets injected into every agent's LLM prompt and embedded into that agent's RAG collection. |
| `agent_modes` | `{ business_id, agent, mode: "manual"\|"auto", auto_thresholds }` |
| `tasks` | `{ business_id, agent, action_type, payload, requires_asset, asset_id, status, owner_feedback, created_at, decided_at, executed_at }` — the universal approval/execution object every agent action passes through. |
| `media_assets` | `{ business_id, task_id, file_ref, media_type, agent_review: { verdict, notes }, uploaded_at }` |
| `credentials` | `{ business_id, provider, encrypted_payload, encryption_key_id, connected_by_user_id, connected_at, scopes }` — encrypted vault, no plaintext ever stored. |
| `chat_threads` | `{ business_id, agent, messages: [{ role, content, created_at }], updated_at }` |
| `decision_logs` | Existing — full audit trail of every agent decision and task transition. |
| `agent_snapshots` | Existing — point-in-time agent state, used for history/replay. |
| `events` | Existing raw event bus records — what triggered what. |

**Indexing:** index `business_id` on every collection above (it's the primary tenant-scoping filter on nearly every query); index `status` on `tasks` (the approval queue polls by status); index `provider` + `business_id` on `credentials`.

---

## 4. Backend Layer (FastAPI) — Full Module & Endpoint List

### 4.1 Core modules (existing, keep)
`main.py` (app + lifespan), `config.py`, `core/llm.py` (Groq client), `core/security.py` (JWT/bcrypt), `database/mongodb.py`, `database/utils.py`, `models/*.py` (Pydantic schemas).

### 4.2 New/extended modules
- `services/credentials.py` — envelope encryption; the only module allowed to decrypt a secret, and only inside `execute_task`.
- `services/tasks.py` — `create_task()`, `execute_task()`, `transition_task()` — the shared pipeline every agent calls.
- `services/embeddings_router.py` — generalizes today's Finance-only RAG wiring so every agent gets its own namespaced ChromaDB collection.
- `agents/tools/` — one file per external integration an agent can call (`instagram.py`, `website_cms.py`), each function taking `business_id` and internally resolving credentials — the LLM never sees a token.

### 4.3 Full route list

**Auth** (existing)
- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`

**Businesses & profile**
- `POST /api/businesses`, `GET /api/businesses`, `GET /api/businesses/{id}` (existing)
- `POST /api/businesses/{id}/profile` — create/update `business_profiles`
- `POST /api/businesses/{id}/profile/context` — add a context note/doc, triggers re-embedding

**Agents** (existing, extended)
- `GET /api/agents/{id}/status`, `GET /api/agents/{id}/history` (existing)
- `POST /api/agent-actions/{agent}/trigger` (existing manual trigger — now routes through `create_task`)
- `GET/PUT /api/businesses/{id}/agents/{agent}/mode` — manual/auto toggle + thresholds

**Tasks**
- `GET /api/businesses/{id}/tasks?status=` — approval queue
- `POST /api/tasks/{id}/approve`, `POST /api/tasks/{id}/reject`, `POST /api/tasks/{id}/request-changes`

**Media assets**
- `POST /api/tasks/{id}/assets` — owner upload against a task
- (internal) agent review runs automatically on upload

**Credentials**
- `POST /api/businesses/{id}/credentials/{provider}/connect`
- `DELETE /api/businesses/{id}/credentials/{provider}`
- `GET /api/businesses/{id}/credentials` — names + `connected_at` only, never secrets

**Chat**
- `POST /api/businesses/{id}/agents/{agent}/chat`
- `GET /api/businesses/{id}/agents/{agent}/chat`

**Events & simulation** (existing)
- `GET/POST /api/events`
- `POST /api/simulation/{id}/start|stop|pause|resume`, `GET /api/simulation/{id}/logs`, `GET /api/simulation/{id}/summary`

**Admin** (role = admin only)
- `GET /api/admin/businesses`, `GET /api/admin/businesses/{id}`
- `GET /api/admin/system-health`
- No admin route ever imports `services/credentials.py`.

**Policies** (existing, still used for threshold config underneath `agent_modes`)
- `GET/PUT /api/policies/{business_id}/{agent}`

### 4.4 The task pipeline, precisely
1. Agent decides to act → calls `create_task(agent, action_type, payload, requires_asset)`.
2. If `requires_asset`: status → `awaiting_asset`, wait for upload + agent review.
3. Check `agent_modes`: **auto + within threshold** → `auto_approved` → immediately `execute_task()`. **Manual, or auto but outside threshold** → `pending_approval`, sits in the owner's queue.
4. Owner approves/rejects/requests changes → on approve, `execute_task()` runs, calling the relevant `agents/tools/*.py` function, which resolves credentials just-in-time.
5. Every transition writes to `decision_logs`.

### 4.5 Testing (existing `backend/tests/` + new)
Keep `test_api, test_auth, test_agents, test_agent_actions, test_businesses, test_negotiation, test_policies, test_rag, test_simulation`. Add `test_tasks.py`, `test_credentials.py` (assert encryption round-trips and that no admin-reachable function can decrypt), `test_chat.py`, `test_admin.py` (assert role gating).

---

## 5. Frontend Layer (Next.js) — Full Page & Component List

### 5.1 Public / auth
- `/login`, `/register` — split-screen per the existing design brief (see design system doc).

### 5.2 Owner app
- `/setup` — multi-step wizard: company info → agent selection → **full business profile** (brand, product, marketing channels, finance caps, operations) → **connect accounts** (Instagram/website via OAuth-style flow) → RAG context upload → deploy.
- `/dashboard` — KPI cards, dual-axis telemetry chart, live agent terminal feed, event injector, **task queue panel** (approve/reject/request-changes inline).
- `/agents/[agent-id]` — existing per-agent tabs **plus**: mode toggle (manual/auto + thresholds), chat panel, and for Marketing, the asset-request card (upload + agent review verdict).
- `/memory-inspector` — vector search, now filterable across all five agents' collections, not just Finance.
- `/system-health` — existing infra status view.
- `/about` — existing credits page.

### 5.3 Admin app (new, role-gated)
- `/admin` — overview: total businesses, active simulations, recent signups.
- `/admin/businesses` — table of all businesses.
- `/admin/businesses/[id]` — detail (metadata + activity only, never credentials).
- `/admin/system-health` — admin view of the same infra data.

### 5.4 Frontend state (Redux slices)
Existing: `authSlice, businessSlice, agentsSlice, eventsSlice, simulationSlice`.
New: `profileSlice` (business_profiles), `taskSlice` (approval queue), `chatSlice` (per-agent threads), `credentialsSlice` (connection status only, never secret values), `adminSlice`.

### 5.5 Frontend tests
Component tests for: task queue actions, mode toggle, chat panel send/receive, asset upload + review display, admin table role-gating (a non-admin hitting `/admin/*` should redirect, not just hide nav).

---

## 6. Security Requirements (non-negotiable, applies across all three layers)
- Roles enforced server-side only (`require_admin` dependency), never trusted from the frontend.
- Envelope encryption for all third-party credentials; decryption happens only inside `execute_task`, in memory, never logged, never placed in an LLM prompt.
- Admin code path has zero access to the `credentials` collection — enforced by not exposing any admin-callable method in `services/credentials.py`, not just by route permissions.
- Every task transition and every credential connect/revoke is written to `decision_logs` with `user_id` + timestamp.
- `.env` files never committed; secrets injected via environment at deploy time (Jenkins → EC2 already does this pattern for other config).

---

## 7. Build Order (execute in this sequence)

1. **Data + roles foundation** — `role` on users, `business_profiles` collection + routes, migrate setup wizard.
2. **Task/approval pipeline** — `tasks`, `agent_modes`, `create_task`/`execute_task`, task queue UI. Wire Finance agent through first as the reference implementation.
3. **Credential vault + first live integration** — encryption service, Instagram connect flow, Marketing's `post_to_instagram` tool.
4. **Media asset flow** — `media_assets`, upload endpoint, agent review, Marketing asset-request UI.
5. **Chatbot** — `chat_threads`, chat endpoint + panel, routed through `create_task` (no bypass).
6. **Admin interface** — admin routes + `/admin/*` UI, explicit credential-isolation test.
7. **RAG expansion** — generalize ChromaDB wiring to all five agents, update memory inspector.
8. **Hardening** — audit log review, rate limiting on chat/task-creation, persist `registry.py` agent-manager state so a server restart doesn't lose live simulations.

---

## 8. Deployment (existing infra, unchanged)
Docker Compose for dev (`docker/docker-compose.yml`); Jenkinsfile builds, tests, pushes to ECR, deploys to EC2 via `docker-compose.prod.yml`. New environment variables to add as this plan is built: `MASTER_ENCRYPTION_KEY` (or KMS reference), `INSTAGRAM_CLIENT_ID/SECRET`, any additional provider OAuth credentials — added to `.env.example` with placeholder values, real values only ever set on the deploy target, never committed.
