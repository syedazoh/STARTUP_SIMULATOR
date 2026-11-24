# Independent role-worker launch simulation

Seven additional **analysis worker configurations** run CEO → Marketing → Finance → HR → Operations → Support → Strategy. They preserve the existing five agent runtimes and their authoritative approval/execution path; Support and Strategy are distinct read-only workflows, not renamed departments. This is the supplied brief's role assumption, not claimed supervisor approval. Source: `models/distributed_schemas.py`, `services/distributed.py`, `role_worker.py`, `api/routes/distributed.py`.

## Contract and authority

Owner-authenticated `POST /api/businesses/{business_id}/distributed-runs` accepts `idempotency_key`, seed, goal, campaign name, requested budget in minor units, synthetic ticket and duration (10–3600 seconds). Unknown fields are rejected; identity comes from the authenticated owned business. Scenario currency is explicitly USD, matching the existing dollar-based simulator; no foreign exchange is inferred. All market opportunities/tickets/content/outcomes are synthetic. The same key/body returns the same run, another body conflicts. GET list returns the latest 20; GET `/{run_id}` returns bounded seven-role progress, artifacts and saved task outcome. Reads also reconcile durable progress.

The existing Mongo jobs collection is the durable transport. Version-one envelopes carry event/correlation IDs, role and predecessor. Job identity is deterministic per run/role; the run identity includes the business. Each worker claims only its role; the API's existing worker explicitly excludes role messages. Claims are atomic, fenced by a random lease token and an unexpired lease. A role has a 45-second lease, 30-second handler timeout and three attempts with bounded backoff. Expired claims recover after crash; malformed/unauthorized messages go to `dead_letter`. Cancellation/timeout fences running writes, and shutdown leaves uncommitted work recoverable. Results and completion status persist in one job update. A lost lease cannot publish success. This is at-least-once analysis, **not exactly-once external execution**.

The API's optional background loop reconciles persisted predecessors; polling GET also repairs the next job if the API restarts or background scheduling is off. Only a succeeded predecessor permits the next role. Deadline checks stop further scheduling; API loop/polling is required to finalize `timed_out` when all workers are down. This dependency is explicit. No replica of AgentRegistry is constructed in a role worker. Existing API runtimes remain single-process for effect execution.

## Rules and outputs

- CEO records goal/opportunity and delegation intent.
- Marketing saves a rule/template content draft without invented discount, performance or customer claims.
- Finance reads structured unreserved cash (or explicitly initial budget before an account exists), recommending at most 10%; it reserves nothing. Strategy also caps its recommendation against current cash and the saved Finance ceiling.
- HR/Operations disclose initial headcount/resources as references, flag staffing/fulfillment review and do not pretend those references prove current capacity. Actual hiring/resources need separate approved tasks.
- Support searches only ready, versioned, Support-authorized documents through the existing freshness/ACL-filtered retriever. It saves exact excerpts with citations, or an abstaining draft and owner escalation. It does not invent a refund/fulfillment promise. Upload documents with department `support`; these independent analysis roles are valid document departments without adding in-memory execution agents.
- Strategy records a no-spend baseline, a bounded-launch alternative and risks; this rule predicts no ROI.

`POST /{run_id}/proposal` is available only after seven results. It creates one deterministic existing `campaign_launch` task with explicit owner review. Existing CEO validation, immutable preview, Finance/ledger bounds and execution apply; workers cannot approve, hire, publish or mutate accounts. The existing command center reviews it. The run report reads the persisted task status/result; recommendations and executed results remain distinct. A changed ledger may invalidate an earlier recommendation. Owner-requested revisions use the existing implementation: new reviewable content or an explicit blocked state; unchanged proposals cannot be accepted as revised.

Current new workflows are rule-based/extractive, not AI-generated content acceptance. Full model-assisted output/quality comparison, current staffing/capacity services and richer seven-role negotiation remain partial in the matrix. Existing Chroma decision memory and versioned corpus storage are preserved.

## Run locally

Keep existing `.env` files. Start real MongoDB and the normal backend. Enable `BACKGROUND_JOBS_ENABLED=True` for automatic coordination/indexing. In **seven separate terminals/processes**, using the same backend environment/database:

```bash
cd backend
python -m app.role_worker --role ceo
# Repeat with marketing, finance, hr, operations, support, strategy.
```

A shared backend image may use the same command override per service. Workers require Mongo and fail startup when unavailable; there is no in-memory fallback. They use no provider credentials for these rules. POST a run with `{"idempotency_key":"demo-1","seed":17,"requested_budget_minor":500000}` using your normal authenticated API client. Poll run progress, inspect all seven outputs, create a proposal, then review/approve it in the command center. Do not use production data to rehearse. Cancellation affects only this analysis; an already-created approval task has its own lifecycle. Retrying a dead letter requires a new reviewed run/key; generic failed-job retry excludes the `dead_letter` status.

## Reproducible process acceptance

Use an isolated Mongo instance and a disposable test database (the test generates its own name and drops only that name):

```bash
PYTHONPATH=backend MONGODB_INTEGRATION_URL=mongodb://127.0.0.1:27029 \
  python -m pytest backend/tests/integration/test_distributed_processes.py -qs
```

The test launches a real HTTP API plus seven separate role-worker processes, kills a separate claim process immediately after its durable claim, accelerates lease expiry, verifies recovery, saves all outputs, creates/reviews/executes a campaign and checks duplicate approval cannot duplicate ledger state. It prints PIDs/mode/duration without credentials. On 24 November: seven unique worker PIDs distinct from the API, recovered CEO attempt 2, campaign executed; 11.799 seconds for this one cold local synthetic scenario. That single observation is not a p50/p95 or cloud/model benchmark. Focused distributed/jobs/knowledge/revision plus process acceptance: 29 passed. Fixtures and local HTTP tests do not prove live provider delivery or AWS deployment.
