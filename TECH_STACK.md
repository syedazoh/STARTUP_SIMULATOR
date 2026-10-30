# Complete Tech Stack

Every technology used in the project, layer by layer, with what it's for and why it was chosen. Keep this file updated as the stack evolves — it's the reference for onboarding and for any "why are we using X" question.

---

## Frontend

| Technology | Purpose |
|---|---|
| **React + Vite** | SPA frontend with React Router; Vite provides development serving and production builds. |
| **Tailwind CSS** | Utility-first styling, implements the design system tokens directly as config (colors, spacing, radius from `FRONTEND_DESIGN_SYSTEM.md`). |
| **Framer Motion** | All UI animation — page transitions, modal entry, terminal line animation, task-resolve micro-interaction. |
| **Recharts** | Dashboard charts — dual-axis revenue/burn line chart, sentiment timeline, Finance agent's budget pie chart. |
| **Lucide Icons** | Icon set — consistent stroke-based icons across nav, buttons, status indicators. |
| **Redux (Redux Toolkit)** | Global client state — auth, business, agents, events, simulation, plus new slices for tasks, chat, profile, credentials (status only), admin. |
| **Axios** | HTTP client (`api/client.js`) — wraps all REST calls to the backend with auth headers attached. |
| **WebSockets (native or socket.io-client)** | Live updates — agent terminal feed, task queue changes, simulation tick updates, without polling. |

---

## Backend

| Technology | Purpose |
|---|---|
| **FastAPI (Python)** | Core backend framework — REST API, auto-generated OpenAPI docs at `/docs`, dependency-injection-based auth guards. |
| **Uvicorn** | ASGI server running FastAPI, supports the `--reload` dev workflow and WebSocket connections. |
| **LangGraph** | State-machine framework for each agent (CEO, Marketing, Finance, Operations, HR) — models each agent's decision flow as a graph of steps rather than a single prompt call. |
| **Groq API (Llama-3)** | The LLM provider — fast inference for agent reasoning and generation (campaign copy, support replies, financial analysis, strategic directives). |
| **Pydantic** | Schema validation for every request/response and for structured LLM outputs (`agents/schemas.py` — e.g. `HRDecision`) so agent output is always typed, not free text. |
| **python-jose + bcrypt** | Authentication — JWT issuance/verification and password hashing. |
| **Motor / PyMongo** | Async MongoDB driver used by `database/mongodb.py`. |
| **ChromaDB** | Vector database for agent long-term memory (RAG) — one namespaced collection per business per agent. |
| **Sentence-transformers (or Groq/OpenAI embeddings, whichever `rag/embeddings.py` uses)** | Generates the embeddings stored in ChromaDB. |
| **cryptography (Fernet/AES via `cryptography` package)** | Envelope encryption for the credentials vault — encrypts third-party tokens (Instagram, website CMS) at rest. |
| **pytest** | Backend test suite — unit and integration tests per module (`test_api`, `test_agents`, `test_rag`, etc.), config in `pytest.ini`. |

---

## Database & Storage

| Technology | Purpose |
|---|---|
| **MongoDB** | Primary datastore — all collections (users, businesses, business_profiles, tasks, credentials, chat_threads, decision_logs, etc.). Chosen for schema flexibility, which matters since `business_profiles` and agent payloads are naturally document-shaped JSON, not rigid rows. |
| **MongoDB Atlas** (per the project brief) | Managed hosting for MongoDB in non-local environments. |
| **ChromaDB** | Vector store for RAG memory — separate from MongoDB because it's optimized for similarity search, not transactional document storage. |
| **Object storage (e.g. AWS S3, or local disk in dev)** | Storage for uploaded media assets (reels/images submitted for agent review) — the `media_assets` collection stores a `file_ref` pointing here, not the binary itself. |

---

## AI / Agent Layer

| Technology | Purpose |
|---|---|
| **LangGraph** | Orchestrates each agent's internal multi-step reasoning (evaluate → decide → produce structured output). |
| **Groq (Llama-3)** | The underlying LLM every agent calls into. |
| **Custom event bus (`orchestration/event_bus.py`)** | Not a third-party message queue — a lightweight in-process pub/sub scoped per business, since agent-to-agent coordination only needs to happen within one business's simulation, not across the whole system. |
| **ChromaDB + embeddings pipeline** | Gives agents recall of past decisions specific to their own domain and business. |

---

## Security

| Technology | Purpose |
|---|---|
| **JWT (python-jose)** | Short-lived access JWTs backed by revocable server-side sessions and rotating refresh cookies. |
| **bcrypt (direct API)** | Password hashing. |
| **cryptography (Fernet)** | Encrypting third-party credentials before they touch the database. |
| **Environment-injected credential master key** | Protects each user's per-account data key. Inject a deployment-specific key; the application does not directly integrate with KMS. |

---

## Infrastructure & DevOps

| Technology | Purpose |
|---|---|
| **Docker + Docker Compose** | Containerizes backend, frontend, and MongoDB for identical dev/prod environments (`docker/docker-compose.yml` for dev, `docker-compose.prod.yml` for prod). |
| **Jenkins** | CI/CD pipeline — builds images, runs the test suite, pushes to ECR, deploys to EC2 (`Jenkinsfile`). |
| **AWS EC2** | Hosts the running containers in production. |
| **AWS ECR** | Container image registry Jenkins pushes to before EC2 pulls and deploys. |
| **GitHub Actions** | CI checks on pull requests — `backend-tests.yml`, `frontend-tests.yml` run automatically on every PR, separate from the Jenkins deploy pipeline. |
| **Nginx** | Serves the built frontend in production (`frontend/nginx.conf`). |

---

## Dev Tooling

| Technology | Purpose |
|---|---|
| **VS Code** | Primary editor, with the Python interpreter pinned to `backend/venv` (`.vscode/settings.json`). |
| **Git + GitHub** | Version control and collaboration — see `TEAM_SETUP_AND_TESTING_GUIDE.md` for the team workflow. |
| **Postman / Insomnia** | Manual API testing against the FastAPI backend. |
| **MongoDB Compass** | GUI database inspection during development. |
| **pytest** (backend) / **Jest or Vitest** (frontend, whichever `frontend/package.json` specifies) | Automated test runners for each side of the stack. |
| **ESLint + Prettier** | Frontend linting/formatting consistency. |

---

## Why this stack, in one line each

- **FastAPI over Flask/Django:** async-native, auto-generated docs, and Pydantic validation fit an API that's mostly structured JSON in and out (perfect for LLM-structured-output workloads).
- **LangGraph over a single prompt-chain:** each agent's decision process has real branching (e.g. "does this need approval," "does this need an asset") that a state graph models more honestly than one long prompt.
- **MongoDB over a relational DB:** the core objects (`business_profiles`, task payloads, agent snapshots) are naturally nested JSON that varies per agent — forcing them into rigid tables would mean constant schema migrations.
- **ChromaDB separate from MongoDB:** vector similarity search and transactional document storage are different workloads; using the right tool for each avoids bolting vector search onto a database that isn't built for it.
- **React + Vite:** matches the implemented SPA, React Router routes, and static production bundle.
- **Docker Compose + Jenkins:** keeps "works on my machine" from being a problem — the same containers run in dev and prod, and Jenkins is already wired to the team's AWS setup.
