# Dataset-driven product launch

Implemented additive demo path, November 10, 2026. All data/results are synthetic. This does not complete the broader worker, frontend migration or department roadmap.

## Run it

1. Configure and start the existing FastAPI backend and Next.js app using `docs/SUPABASE_AUTH_SETUP.md`. Production persistence requires MongoDB; the existing debug in-memory fallback loses data on restart. No new dependencies or provider credentials are required by the demo itself.
2. Sign in, select the **Synthetic launch demo** link beside an existing business on `/workspace`. The route is `/workspace/<businessId>/demo`. All five departments must be enabled for proposals.
3. Choose `datasets/product-launch-v1/dataset.json` (or its equivalent `.csv`), select the matching format, and preview. Inspect counts and records, then confirm import. Preview does not write. Validation errors name fields and CSV row numbers where applicable.
4. Propose the default campaign budget: 100000 USD cents ($1,000). Review the forecast and department evidence. An identical proposal returns the same task rather than creating another run.
5. Approve or reject through the existing task routes. Demo approval always requires the owner, even if a department's regular policy is automatic. Approval expires after 24 hours; content is immutable. To change the budget, reject and propose a different budget. To repeat the exact proposal after rejection/expiry, reset and reimport.
6. After approval, inspect recorded metrics, baseline, CEO report, task ID, dataset/proposal digests and reference citations. Refresh/reload reads persisted results; retrying an already executed demo approval returns its existing result. An interrupted approved task can resume through the same approval endpoint.
7. Preview reset, type `RESET SYNTHETIC DEMO`, and confirm. The designated import generation is archived; pending demo tasks are cancelled; completed results/approval/audit history remain. Accounts, businesses, regular tasks, credentials and actual financial accounts are untouched. Reimport the same sample to obtain a fresh generation.

## Shared data and agent boundary

`demo_datasets` stores one bounded, immutable snapshot per `(business_id, dataset_id)` using a deterministic unique Mongo `_id`. JSON and CSV normalize to the same SHA-256. The API derives business access through existing owner dependencies; uploaded owner/business identifiers fail validation. The same dataset ID with different content returns 409. Identical reimports replay the active import; explicit reimport after reset creates a new generation.

Each scenario uses five **deterministic department adapters**, not live LangGraph/LLM decisions:

- Marketing reads goals/campaigns/products and proposes the owner-selected budget.
- Finance reads structured sales/expenses/capital and checks affordability.
- HR reads staffing and fictional candidates. Applicants never count as employees.
- Operations reads stock, pending orders and staffed capacity.
- CEO reads those facts and records an evidence-linked summary.

All use `department_records` with the same import digest. HR candidate records are excluded from other department record views. These are trusted internal services behind owner-authorized endpoints, not a new agent identity or permission system. Regular simulations and chat retain their existing behavior; this feature does not inject demo records into live agent prompts or real accounting.

References are filtered by business and department **before** lexical ranking. Up to three overlapping documents augment review/report evidence with import ID, document ID, title and version. No-match retrieval returns no invented citation. This small-corpus retrieval path needs no embedding model; it is not the planned hybrid/vector RAG upgrade. Reference text is untrusted and cannot authorize actions or supply numerical balances.

## Rules: launch-v1

All math uses typed records and integer cents. No stochastic choices; no seed is necessary. Each task is an independent branch from the imported starting state, not another sequential spend against it.

- Opening cash = starting capital + historical sales − historical expenses.
- Block approval if proposed budget exceeds opening cash.
- Fulfillment capacity = existing staff units/day × campaign duration.
- Pending units receive priority, limited by stock and capacity.
- Reach = floor(budget cents × reach-per-100-cents / 100).
- New demand = floor(reach × conversion basis points / 10000).
- New units fulfilled = min(new demand, stock remaining after pending units, capacity remaining after pending units).
- Revenue = (fulfilled pending + fulfilled new units) × price.
- Cost of goods = fulfilled units × unit cost. This measures contribution; opening inventory is prepaid and is not charged again to cash.
- Contribution = revenue − cost of goods − campaign budget.
- Ending cash = opening cash − campaign budget + revenue.
- Remaining stock = starting remaining stock − total fulfilled units.
- Goal met = new units fulfilled meets target and launch date + duration is no later than goal due date.

The sample produces 100 new fulfilled units, 5 pending units fulfilled, $5,250 revenue, $2,150 contribution, $23,750 ending cash and 45 units remaining. The fixed $250 baseline produces 25 new fulfilled units. These are assumptions-driven synthetic outcomes, not forecasting accuracy or sales evidence. Excess demand is reported as unfulfilled; no candidate hiring, restocking, tax, refunds or real provider execution occurs.

Rule version, immutable proposal digest, dataset digest, approval expiry and owner identity bind execution. A changed rule version requires a new proposal. Demo execution branches from the existing `execute_task` entry point before live agents, ledger or external handlers. A single conditional task write persists result/status together; replay cannot consume stock or repeat spending.

## Evaluation

`evaluation/cases.json` is separate from the demonstration file and is never ingested by the importer. It covers low capacity, low inventory, zero demand and high demand. Fixed proposal budget and fixed smaller-budget baseline use identical case inputs. Some proposals lose to the cheaper baseline; report all cases. This is a held-apart rules regression set, not a statistically independent assessment of AI quality or real-market prediction. Do not tune rules on these fixtures and then claim held-out performance.

From `backend/`:

```bash
python -m scripts.evaluate_demo
python -m pytest tests/test_dataset_schema.py tests/test_dataset_import.py tests/test_demo_rules.py tests/test_demo_api.py -q
```

Recorded output: `datasets/product-launch-v1/evaluation/results.json`. Data dictionary and JSON Schema: `datasets/product-launch-v1/README.md` and `schema.json`.

## API

All routes below require existing authenticated business ownership:

- `POST /api/businesses/{business_id}/demo/imports`: multipart `file`, `format=json|csv`, `action=preview|commit`, and `expected_digest` for commit.
- `GET /api/businesses/{business_id}/demo`: active datasets and their tasks/results (first 100 imports/tasks per import in this demo UI).
- `GET .../demo/{import_id}/records/{department}`: scoped structured view.
- `GET .../demo/{import_id}/references/{department}?q=...`: authorized reference retrieval.
- `POST .../demo/{import_id}/launch`: `campaign_id`, integer `budget_minor`.
- `GET .../demo/{import_id}/reset`: preview designated scope.
- `POST .../demo/{import_id}/reset`: dataset `digest`, exact confirmation phrase.
- Existing `/api/tasks/{task_id}/approve` and `/reject` decide demo tasks. `/revise` and `/release-budget` reject this demo action.

Files are limited to 1 MiB. Next.js permits 2 MiB action envelopes to accommodate multipart overhead, while the API retains the smaller file limit. Imports are single-document writes; no multi-collection transaction or data migration is introduced. Invalid files write nothing. Reset is archival, not data deletion. A racing execution may finish an already approved isolated branch while reset archives it; it cannot affect live data. Historical evidence remains available via the existing task list.

## Verification boundaries and rollback

API tests use disposable Mongo doubles and controlled identity verification. Browser acceptance uses a disposable local identity service and Mongo double, not real Supabase/Atlas. Verify real Mongo persistence and live Supabase separately using the existing project acceptance checks. Embedding-dependent legacy RAG tests need their separate sentence-transformers installation/model.

Rollback by reverting the feature commits. No backfill, account migration, live communication, spending, deployment or publication is included. The added collection can remain dormant; never delete shared business data to roll back this feature.
