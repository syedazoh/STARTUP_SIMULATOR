# Startup Simulator - Multi-Agent AI-powered Business Simulation Platform

## Jobs, deadlines, private MCP and document RAG — 17 November 2026

Plan: [automation and knowledge](docs/AUTOMATION_KNOWLEDGE_PLAN.md). In Next.js, open your business, then **Jobs, deadlines, knowledge & MCP**.

| Feature | Implemented | Boundary |
| --- | --- | --- |
| Background jobs | Durable Mongo queue, idempotency keys, atomic leases, three attempts/backoff, restart recovery, progress/cancel/safe retry | One API process/agent registry; Redis is an optional wake hint, not the queue. Uncertain effects require reconciliation. |
| Queued work | CEO draft plans, saved-task briefs, document indexing and approved internal simulation execution | Drafts require review/activation. Worker execution excludes live email/social/payment effects. |
| Deadlines | Versioned UTC dates, reasoned pending-task edits, in-app reminder/overdue/CEO-owner escalation and execution cutoff | No email/calendar delivery. Approval freezes the deadline. |
| Private MCP | Official SDK stateless Streamable HTTP `/mcp/`, revocable 15-minute business/department capabilities, request budgets | Read budget/task/knowledge or propose internal work. No approve/publish/credentials tool; not a full public OAuth server. |
| Advanced document RAG | Heading/overlap chunks, source/version/department metadata, BM25+dense reciprocal-rank fusion, cached CrossEncoder reranking, strict evidence prompt, exact-quote checks and abstention | Markdown/text only, separate from Chroma decision memory. Visible lexical/extractive fallback when models are unavailable. Citation checks do not establish semantic entailment. |
| Planner evidence | CEO draft planning retrieves CEO-authorized documents | Documents never grant approval or override live ledger/status APIs. Department-scoped evidence is exposed through MCP; automatic consumption across every agent is not implemented. |

### Local setup — Windows Git Bash

Keep existing `.env` files; do not overwrite configured secrets. Python 3.11 is the supported Docker/CI version. From the repository root:

**Terminal 1 — backend**

```bash
source .venv/Scripts/activate
cd backend
python -m pip install -r requirements.txt
# Edit backend/.env: BACKGROUND_JOBS_ENABLED=True
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If your virtual environment lives inside `backend`, activate `backend/.venv/Scripts/activate` instead. Linux/macOS activation ends in `bin/activate`. Require `http://127.0.0.1:8000/health` to report `mongo: connected`. Automation refuses volatile in-memory storage. Restart after `.env` changes.

**Terminal 2 — Next.js frontend**, from the repository root:

```bash
cd web
npm ci
npm run dev
```

Open `http://localhost:3000`; sign in with your **application user's email/password**, choose your business and open automation. `web/.env.local` needs `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` and `BACKEND_URL=http://127.0.0.1:8000`. Backend `.env` uses `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` without `NEXT_PUBLIC_`. Never expose service-role/backend secrets in browser variables. Existing Vite/3D boardroom remains separately available on port 5173.

### Model cache and knowledge

Run once from `backend`, with its environment activated and internet access:

```bash
PYTHONPATH=. python scripts/warm_knowledge_models.py
```

This explicitly downloads `sentence-transformers/all-MiniLM-L6-v2` and `cross-encoder/ms-marco-MiniLM-L-6-v2` to the local Hugging Face cache. Inspect model licenses before changing models. Runtime downloads default off (`RAG_ALLOW_MODEL_DOWNLOAD=False`); Docker builds warm both caches. Upload `.txt`/`.md`, select allowed departments, queue indexing and inspect job status. Use **Reindex** after warming models if a document previously lacked vectors; it increments the source version. Updates/deletion invalidate old retrieval and stale jobs cannot restore them.

Ask a question under an authorized department. Inspect `mode`, `dense_status`, `reranker`, `answer_mode`, source versions and citations. Missing model/API access yields a labelled fallback or abstention. No false hybrid/AI-success claim is made. Bounds: 100 documents, 128 chunks per document, 2,048 chunks per retrieval corpus. Normalized vectors live in Mongo and a bounded authorized corpus is scored; this is **not Atlas Vector Search** or a large indexed vector service. PDF/OCR is deferred.

### Use jobs and deadlines

1. Queue a CEO goal, follow its saved job result, then review/activate the draft in the Command Center.
2. Preview an internal task and choose **Approve and queue**. CEO authorization and the current approval fingerprint are still required. Existing **Approve and execute** remains available. After timeouts, refresh before repeating; API callers must reuse the original idempotency key for unchanged requests.
3. Set a pending task's due date/time and reason. The UI converts your device timezone to UTC. Set reminder minutes before and escalation minutes after; notifications appear here. Deadline edits supersede old notifications. Expired work cannot begin through either execution path.
4. Queue an on-demand task-status brief. Its counts/task IDs describe at most 200 recent saved tasks, not real-world business success.
5. Cancel queued/retry jobs only. Failed drafting/index jobs can be retried. Running work is not UI-interruptible; uncertain executing effects require evidence review. Processing is sequential, with 120-second attempt timeout and 180-second lease.

Redis is optional: `REDIS_URL=redis://127.0.0.1:6379/0`. To run local infrastructure:

```bash
docker compose -f docker/docker-compose.yml up -d mongo redis
```

Use the Python/Next terminals above. The full existing Compose frontend is **Vite**, not Next.js. The development backend worker is enabled in Compose. Redis outages fall back to durable Mongo polling; no task payload/token is placed in Redis. Do not use multiple Uvicorn workers/replicas with this in-process agent registry. No production deployment is performed here.

### Connect a private MCP client

Select allowed departments and mint a 15-minute token in automation. Proposal permission is optional and still requires fresh owner review. Configure a trusted MCP client with `http://localhost:8000/mcp/` and `Authorization: Bearer …`. The token is shown only in the current tab and is not saved to local storage. Revoke it explicitly; application logout does not revoke an independently minted capability. Expiry/revocation is also rechecked before queued MCP proposals run.

Official SDK smoke client, from `backend`:

```bash
python scripts/check_mcp.py
```

It privately prompts for the capability and initializes/lists tools without executing work. Tools: `get_budget`, `get_task_status`, `search_knowledge`, `propose_task`. Tenant identity comes from the token, never tool arguments. App native/Supabase tokens cannot replace MCP capabilities. Hosted MCP requires operator-configured HTTPS `/mcp/` routing, `MCP_RESOURCE_URL`, `MCP_ALLOWED_HOSTS` and allowed origins, followed by newly minted tokens. Existing production proxy routing is not automatically changed.

### Verification and manual acceptance

Automated tests cover idempotency/leases/retry recovery, deferred approval, tenant isolation, deadline versions/cutoff, MCP wire access/revocation and source deletion/fallbacks. The verified application passed 475 backend tests, Docker wiring/restart, Next build/types/tests/audit and browser acceptance, including 320/390/768 px layouts. An official MCP SDK client also passed a disposable real local HTTP smoke. Run links and the operator-client follow-up are in [impact log](docs/impact.md).

From `backend`:

```bash
python -m pytest tests/test_automation_jobs.py tests/test_automation_api.py tests/test_private_mcp.py tests/test_knowledge.py
PYTHONPATH=. python scripts/evaluate_knowledge.py --output knowledge-evaluation.json
# After cache warm-up, require actual hybrid/cross-encoder execution:
PYTHONPATH=. python scripts/evaluate_knowledge.py --require-hybrid --min-pass 49 --output knowledge-evaluation.json
```

The **50 synthetic cases** run in an isolated mocked database with no LLM calls. Results record lexical baseline versus actual pipeline and modes; this tests retrieval coverage and department isolation, not factual entailment or customer-data quality. CI measured lexical baseline 48/50 and actual hybrid/cross-encoder retrieval 50/50 on this same synthetic corpus; this is limited retrieval evidence, not a real-data quality claim. Run links and final verification are recorded in [impact log](docs/impact.md).

Manual acceptance with a test business: verify Mongo/worker heartbeat; complete a brief; set a deadline and observe an in-app reminder; upload/reindex a policy and inspect citations; mint/revoke MCP access; approve/queue internal work and verify its saved result survives a backend restart. Production hosting, provider credentials and real-data acceptance remain operator tasks.

## Project Overview

Startup Simulator is a comprehensive multi-agent AI-powered business simulation platform designed to model complex business operations through autonomous agents managing different departments of a startup.

## Current implementation (November 2026)

The application now has a redesigned public website and **two distinct authenticated workspaces**:

| Screen | Purpose | Main features |
| --- | --- | --- |
| **Command Center** | Manage and monitor the business | Simulation start/pause/resume/stop, cycle and agent KPIs, pending owner approvals, event activity, Finance/Marketing history charts, end-of-run summary, and a link to the Boardroom |
| **3D Boardroom** | Inspect collaboration visually | Large WebGL scene with five selectable humanoid agents, an agent spotlight with backend state and pending work, an event/activity timeline, filters for all or selected-agent events, and a link to each agent workspace |

The Boardroom is a **separate page**, not a duplicate of the Command Center. The frontend also includes registration, login, onboarding, business selection, department agent pages, decision history, agent memory, business profile, and protected administration routes.

### UI/UX and 3D work completed

- Responsive public landing page with sections for the executive team, simulation workflow, and platform features.
- Responsive authenticated navigation and business switcher.
- Emerald, Champagne, Lavender, and Ivory design system with updated typography and focus styling.
- React Three Fiber + Three.js boardroom with a conference table and **procedurally modeled 3D humanoid characters** for CEO, Finance, Marketing, HR, and Operations. These are real WebGL meshes, **not photos, static images, or imported/rigged GLB models**.
- Clickable/selectable 3D executives and an accessible list-view alternative; reduced-motion preferences are respected.
- Communication beams for recognized backend agent-to-agent event types. The UI does not invent conversations, and old events are not replayed as new messages when the view first loads.
- Dedicated Boardroom timeline and selected-agent task/state inspector.
- Backend-sourced simulation status, pending tasks, approvals, decision/event history, and agent metrics.

### Backend integration and current limits

The frontend calls the existing authenticated **FastAPI REST endpoints** using Axios and Redux Toolkit. Visible pages poll approximately every 1.8 seconds for simulation, agent, task, and event changes (the task queue has its own polling interval). **WebSockets/SSE are not implemented**. The backend event bus does not attach a recipient to every event; the boardroom animates only explicitly addressed messages or a small set of established event routes, such as Marketing → Finance budget requests and Finance → CEO arbitration requests. An event counter of zero does not mean the entire simulation has no activity; it reflects what the event-history endpoint returned.

The current 3D agents are stylized geometry, **not detailed rigged characters with facial animation, speech, or cinematic motion**. Richer models, animations, real-time push streaming, and additional browser/GPU accessibility testing are future work. Agent execution depends on backend configuration and available AI services; a UI representation of an agent does not prove an external AI call succeeded.

### Recent merged frontend milestones

- [PR #12](https://github.com/syedazoh/STARTUP_SIMULATOR/pull/12) — initial landing-page redesign, interactive 3D boardroom, Command Center, theme, navigation, backend event routing, and frontend integration.
- [PR #13](https://github.com/syedazoh/STARTUP_SIMULATOR/pull/13) — separate the 3D Boardroom into its own immersive page; keep the Command Center focused on monitoring, approvals, and business analytics; add route-separation regression tests.

## CEO supervision and authentication

The CEO can propose department assignments and review their execution reports. Actions from the UI, chat, event API and deployed simulation pass through task approvals. Authentication uses short-lived access tokens in memory and rotating HttpOnly refresh cookies with server-side revocation.

See [CEO supervision and session guide](docs/CEO_SUPERVISION_AND_SESSIONS.md) for usage, migration, validation and remaining work. Existing sessions require a fresh login after this update.

## Architecture

### Backend (FastAPI - Python)

The backend has four department agents and a CEO supervisor:

1. **Finance Agent** - Manages budgets, revenue tracking, expense management
2. **Marketing Agent** - Handles campaigns, market analysis, customer engagement  
3. **HR Agent** - Manages recruitment, payroll, team performance
4. **Operations Agent** - Oversees supply chain, resource allocation, process optimization
5. **CEO Agent** - Proposes department assignments, authorizes work and reviews execution evidence

### Key Components

- **Event Bus**: Central messaging system for agent communication
- **Agent Manager**: Orchestrates multiple agents and their interactions
- **FastAPI**: RESTful API for frontend communication

### Frontend (React + Vite)

- React 18, Vite 6, React Router, Redux Toolkit, Axios, Tailwind CSS, and Recharts.
- Three.js, React Three Fiber (`@react-three/fiber`), and Drei (`@react-three/drei`) for the interactive 3D scene.
- Polling-based REST API integration (not WebSockets).
- Distinct Command Center and 3D Boardroom, plus responsive public and authenticated layouts.

### DevOps

- Docker containerization (Backend, Frontend)
- Docker Compose for local development
- MongoDB for business records, tasks, financial state and reports
- ChromaDB for retrieval of previous decision summaries
- GitHub Actions CI/CD workflows

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+ recommended (use Node.js 22 for parity with frontend CI)
- Docker & Docker Compose (optional)

### Installation

1. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Git Bash / macOS / Linux; on Windows PowerShell use venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

2. **Frontend Setup**
```bash
cd frontend
npm ci
```

**Important for existing local clones:** The 3D frontend requires `three`, `@react-three/fiber`, and `@react-three/drei`. After pulling the latest `main`, run `npm ci` again in `frontend/`. If Vite reports `Failed to resolve import "@react-three/fiber"`, stop Vite, run `npm ci`, then restart `npm run dev`. Do not disable Vite's error overlay to hide a missing dependency.

### Running the Application

#### Option 1: Local Development

**Backend**
```bash
cd backend
uvicorn app.main:app --reload
```
API will be available at `http://localhost:8000`

Login requires MongoDB, including permission to create the `login_attempts`
TTL index. Each email address (case insensitive) gets five login attempts per
fixed five-minute window, shared across backend workers. All attempts count,
including successful logins. Excess attempts return HTTP 429 with `Retry-After`;
throttled attempts emit a warning without logging passwords or email addresses.
Login returns HTTP 503 if the shared throttle store is unavailable by default.

For temporary local development **without installing MongoDB**, set these in
`backend/.env`:

```dotenv
DEBUG=True
ALLOW_IN_MEMORY_LOGIN=True
```

Restart the backend and register an account. When MongoDB is unavailable, this
explicit opt-in uses a bounded in-memory login budget with the same five-attempt
limit. It only works with `DEBUG=True` and one backend process. Accounts,
sessions, and business records are temporary and disappear on backend restart
or auto-reload; register again afterward. MongoDB remains required in production,
and a failure in an actual MongoDB throttle store still blocks login.

**Frontend**
```bash
cd frontend
npm run dev
```
Frontend will be available at `http://localhost:5173`

#### Option 2: Docker Compose

```bash
# From the repository root, create docker/.env from docker/.env.example first.
docker compose --env-file docker/.env -f docker/docker-compose.yml up --build --renew-anon-volumes
```

See [Docker local setup and troubleshooting](docs/DOCKER_LOCAL_SETUP.md) for Windows commands, health checks, and dependency-volume recovery.

## Project Structure

Key frontend paths:

```text
frontend/src/
  App.jsx                           # Protected routes and screen separation
  pages/Landing.jsx                 # Public marketing site
  pages/Dashboard.jsx               # Command Center: controls, tasks, analytics
  pages/Boardroom.jsx               # Dedicated 3D Boardroom and event timeline
  components/boardroom/
    Boardroom3D.jsx                 # Three.js scene, avatars, interaction
    eventRoutes.js                  # Valid backend agent communication routing
  components/SimulationControls.jsx
  components/TaskQueue.jsx
  store/slices/                     # Redux state and async API requests
frontend/tests/
  boardroomEvents.test.mjs          # Event routing and agent ID regression tests
  boardroom-separation.test.mjs      # Distinct route/screen regression tests
```

Other directories contain the FastAPI backend, Docker Compose setup, project documentation, and CI workflows.

For AI fallback messages or chat failures, see [AI configuration and diagnostics](docs/AI_TROUBLESHOOTING.md).

## Testing

### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
cd frontend
npm ci
npm test
npm run lint
npm run build
```

Frontend CI additionally builds the development container and smoke-tests its API proxy. Docker Compose CI checks backend wiring, approvals, database writes, and restart/session behavior. Automated CI checks are not a substitute for local browser testing of the 3D scene.

### After pulling an updated frontend

```bash
git checkout main
git pull origin main
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`, sign in, and select/create a business. The relevant protected routes are:

- `/b/:businessId/dashboard` — Command Center
- `/b/:businessId/boardroom` — 3D Boardroom
- `/b/:businessId/agents/:agentKey` — individual executive workspace
- `/b/:businessId/decision-log` — decision history
- `/b/:businessId/memory-inspector` — agent memory
- `/b/:businessId/profile` — business profile

A practical smoke test is to start a simulation from the Command Center, inspect status and tasks, open the Boardroom, select an agent, and compare the displayed events and assigned work with the backend. Not every backend event produces a visible communication beam.

## Development Roadmap

Track review findings and validation in [Implementation checklist](docs/IMPLEMENTATION_CHECKLIST.md).
The current backend supports one process. Stored decision retrieval does not train
the language model. Periodic simulation income is demo income, not validated sales forecasting.

- **Weeks 1-6**: Planning & Analysis
- **Weeks 7-10**: UI/UX Design
- **Weeks 11-15**: Agent Development & Enhancement
- **Weeks 17-23**: Integration & Deployment

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Submit a pull request

## License

MIT License

## Synthetic dataset launch demo

The Next.js workspace now links each business to an isolated dataset-driven product-launch demo: preview/import synthetic JSON or CSV, inspect five deterministic department reviews, approve simulated execution, compare results with a fixed baseline and reset only the demo generation. It does not send communications, publish or spend real money. See [setup, rules and verification boundaries](docs/DATASET_SIMULATION.md) and the [sample data dictionary](datasets/product-launch-v1/README.md).
