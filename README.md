# Startup Simulator - Multi-Agent AI-powered Business Simulation Platform

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
