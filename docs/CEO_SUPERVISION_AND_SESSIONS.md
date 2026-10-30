# CEO supervision and revocable sessions

## What changed

The CEO can now turn an owner's goal into a validated draft plan, delegate simulated department actions through the shared task pipeline, and review persisted department execution reports. Owner approval and per-department auto-approval thresholds still apply. A plan does not execute while it is a draft.

Use the CEO agent page to enter a goal, review the proposed assignments and their payloads, and choose **Assign plan to departments**. Review manual tasks in the existing dashboard queue. Return to the CEO page for before/after results and the CEO's recommendation. A `completed` plan means all assignments reached a terminal state; it does **not** mean the business goal was achieved. Check each report for failures and denials.

The owner may still submit department requests directly. Those requests also produce reports to the CEO after execution or owner rejection. The CEO's report review is advisory; it cannot bypass approval rules or execute arbitrary tools.

## API

All CEO routes are scoped to an authenticated business owner.

| Method | Route | Behavior |
| --- | --- | --- |
| POST | `/api/businesses/{id}/ceo/plans` | Accepts `{ "goal": "..." }`; produces a draft and validated assignments |
| GET | `/api/businesses/{id}/ceo/plans` | Lists the most recent 100 plans |
| POST | `/api/businesses/{id}/ceo/plans/{plan_id}/activate` | Atomically claims a draft and creates department tasks |
| GET | `/api/businesses/{id}/ceo/reports` | Lists the most recent 100 departmental reports and CEO reviews |

Plans and reports live in `ceo_plans` and `department_reports`. Reports contain plan/task correlation IDs, objectives, success criteria, the actual result, department before/after state, financial before/after state, and the CEO review. The first planning version supports budget requests, campaigns, recruitment, and resource allocation. It does not let a model put external publishing actions in a plan.

## Execution rules

- Manual actions, chat proposals, the event API, and deployed simulation ticks all use `create_task`. Invalid and disabled-department actions are rejected before insertion.
- Reel requests always require an asset, including when proposed through chat or the event API.
- Task approval and execution use atomic database claims. A competing request receives `409`.
- State mutations are serialized per business **within one application process**.
- Returned provider failures become failed tasks. Denied actions become denied tasks. Exceptions no longer disappear inside the event bus.
- Task and report logs preserve their source and plan/run correlation. Provider error bodies and exception strings are not exposed as task results.
- Do not automatically retry an interrupted `executing` task: an external provider may have accepted the request. Reconcile it first.
- A partially assigned plan becomes `assignment_failed` and cannot be activated again. Inspect existing tasks before proposing a replacement. Activation is not an all-or-nothing multi-document transaction.
- Standalone `SimulationEngine` instances without a submission callback still support direct dispatch for unit tests. The deployed API always supplies the approval callback.

## Authentication

Login issues a default 15-minute HS256 access JWT containing user ID (`sub`), expiry (`exp`), and session ID (`sid`). The frontend holds the access token in memory; old `simulator_token` localStorage entries are deleted. The server checks session revocation and absolute expiry on every protected request, alongside JWT validation and the user lookup.

A random refresh token is stored in a host-only, HttpOnly, SameSite=Strict cookie scoped to `/api/auth`. Production (`DEBUG=false`) also requires Secure cookies. Only SHA-256 hashes of refresh tokens are persisted. Refresh tokens rotate once per refresh; reuse revokes the entire session, including already issued access tokens. Sessions have a fixed absolute lifetime (default seven days).

`POST /api/auth/refresh` restores or renews access. `POST /api/auth/logout` revokes the session and clears the cookie. Both require `X-Requested-With: XMLHttpRequest`; any supplied Origin must match `ALLOWED_ORIGINS`. The browser client uses credentialed requests and coordinates refreshes in a tab, and across tabs using Web Locks where supported. Without Web Locks, simultaneous cross-tab refresh can trigger conservative reuse revocation and require another login.

Cookies assume the production frontend and API share the HTTPS origin configured in Caddy. Local development uses localhost ports, which are the same site. A deployment on different sites needs a deliberate cookie/CORS/CSRF design change; do not loosen origin checks casually.

Environment settings:

| Variable | Default / rule |
| --- | --- |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15; allowed range 1–60 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7; allowed range 1–30 |
| `SECRET_KEY` | Deployment-specific; production rejects blank/default values |
| `CREDENTIAL_MASTER_KEY` | Deployment-specific Fernet key; production rejects blank/default values |
| `ALLOWED_ORIGINS` | Exact frontend origins; preserve the deployed HTTPS origin |

Production Compose and Caddy already configure TLS and required secrets. MongoDB is now mandatory in production; a database outage fails startup rather than silently switching to volatile storage. Development fallback supports the bounded queries and atomic operations needed by the new flows.

**Migration:** Existing stateless JWTs are intentionally rejected. Deploy frontend and backend together and ask users to sign in again. No password reset is needed. Existing users, businesses, tasks, and encrypted provider credentials remain usable. New Mongo collections/indexes are initialized at startup. Back up the database and credential master key before deployment. This branch does not deploy anything.

## Validation

- Backend: `cd backend && HF_HUB_OFFLINE=1 pytest --ignore=tests/test_rag.py --ignore=tests/test_memory_routes.py`
- New focused regressions: `cd backend && pytest tests/test_execution_supervision.py`
- Frontend: `cd frontend && npm test && npm run lint && npm run build`

Backend tests disable external LLM calls globally; individual tests inject structured fake responses or exercise deterministic failure fallbacks. Embedding-store tests need the configured local embedding model and should also run in the normal integration environment. These tests do not prove live Groq responses, Instagram publishing, deployed certificates, or a real MongoDB cluster work.

## Remaining work

This is the first supervision and execution-hardening increment. It does not implement the entire product roadmap.

1. Add a shared financial ledger: budget reservations, recurring payroll, resource costs, attributable sales, and expenses from every department. Replace unconditional periodic demo revenue with explicit scenario economics.
2. Add CEO plan revisions, dependency scheduling, deadlines, target-versus-actual evaluation, and consolidated owner briefings. Review recommendations currently require the owner to initiate a new plan; they do not recursively create unlimited tasks.
3. Separate simulation and live environments at a durable configuration boundary. Complete real OAuth, provider permission/expiry checks, media publication payloads, provider idempotency, and provider revocation before offering live automation.
4. Replace the placeholder brand/media review with honest file validation and real review if needed; add upload size limits, content inspection and durable media storage.
5. Introduce shared job leases and state transactions before multiple workers or instances control businesses. The current per-process execution lock does not provide distributed mutual exclusion.
6. Reconcile interrupted simulations/tasks on startup and provide an operator recovery flow. Add end-to-end tests with real Mongo and a stub provider, plus real-browser session and CEO workflow tests.
7. Add repeatable scenario seeds, a baseline strategy, cost limits, and measurable business outcomes. Keep calculations in deterministic code and strategy proposals in the agents.
