# Implementation checklist

Baseline: `e129cbc06425fcba919750f4563c00e630daf30c`.
The owner authorized implementation after the review. Changes use a review branch;
merging, deployment and real provider actions are separate release steps.

Mark an item complete only after its acceptance checks pass. Partial work does
not close the entire finding. Distinguish test doubles from real Mongo/browser/provider evidence.

## Milestone 1 Trustworthy demo

- [x] R01 Conditional asset attachment prevents stale/terminal transitions.
- [ ] R02 Bounded decoded media validation, honest review and durable storage.
- [x] R03 Summaries distinguish queued work from persisted execution outcomes.
- [ ] R05 Enforce period spending caps and consistent currency semantics.
- [ ] R06 Correct threshold units and separate quantity from total-cost limits.
- [x] R07 Reject invalid weights/limits and disabled-department scenarios.
- [ ] R08 Serialize run admission; durable leases before multiple workers.
- [ ] R09 Record failed/stopped/interrupted outcomes and recover stale runs.
- [ ] R11 Surface required index failures; migrate unique logical keys safely.
- [ ] R15 Scope frontend state across business/session changes.
- [x] R16 Persist final onboarding values after Back edits.
- [ ] R17 Server-side actionable filtering and pagination.
- [ ] R22 Correct unsupported product/documentation claims.
- [ ] R23 Upgrade affected dependencies and verify the resolved graph.

## Milestone 2 Recoverable execution

- [ ] R10 Durable state, approval revisions, attempts and outbox/recovery.
- [ ] R14 Model budgets/deadlines/concurrency and bounded blocking work.
- [ ] R19 Journal capacity admission, archival and audited reconciliation.
- [ ] Process-kill tests after reservation, effects, settlement and evidence writes.

## Milestone 3 Measurable simulation

- [ ] R04 Business clock, causal revenue/churn/capacity, recurring costs and targets.
- [ ] R12 Shared versioned business context for every decision path.
- [ ] R13 Index measured outcomes and evaluate retrieval against a baseline.
- [ ] R21 Accessible/responsive UI, honest states, chart periods and readiness.
- [ ] R22 Held-out comparisons: rules, one planner, multi-agent, outcome memory.

## Milestone 4 Public and live release

- [ ] R18 Verified OAuth/media/receipts and unknown-outcome reconciliation.
- [ ] R20 Abuse controls, least privilege, trusted proxies and key/backup operations.
- [ ] R24 Required CI, real Mongo/browser/provider-stub/restore evidence.
- [ ] Release review before merging/deployment; never replay uncertain effects.

## Execution evidence

Batch 1 implements the immediate integrity and workflow fixes. Unchecked entries
include partially implemented items; they are not represented as fully closed.

| Finding | Implemented in batch 1 | Still required |
|---|---|---|
| R01 | Conditional owned-task/asset attachment, digest, stale/concurrent upload tests | Durable approval revision/attempt design remains R10 |
| R02 | Bounded decoded JPEG/PNG/WebP validation, random storage keys, truthful technical verdict; production request cap and upload volume configured | Video validation deliberately unavailable; deployment/storage restore checks |
| R03 | Deterministic retrospect from persisted task states and settled task expenses; report timestamp | Full causal business metrics remain R04 |
| R06 | Correct quantity/currency labels and manual-mode guidance | Separate enforceable total-cost limits |
| R07 | Finite positive limits, supported event weights, normalized totals, enabled-department filtering | Real deployment verification remains R24 |
| R08 | Serialized admission and active-engine check in the supported single process; concurrent HTTP regression | Durable multi-worker leases |
| R09 | Failed/stopped status callbacks, sanitized error codes, shutdown cancellation and startup interrupted records | Real process-kill and durable recovery tests |
| R11 | Required index exceptions propagate instead of being swallowed | Existing-data deduplication and unique-key migration |
| R15 | Async generation guard and cache reset across account/business creation/switch/logout; route subtree remount | Full browser regression and network cancellation/performance work |
| R16 | Create business only after final review; profile retry reuses saved ID | Full browser/reload validation |
| R17 | Server filters actionable tasks before limiting; regression with 201 newer completed tasks | Stable cursor pagination/counts for more than 200 actionable items |
| R22 | README/landing claims corrected; demo income and non-training memory documented | Other legacy planning docs and held-out effectiveness evaluation |
| R23 | Multipart 0.0.33, Pillow 13.0.0, Axios 1.21.0, Vite 6.4.5; compatible npm audit fixes | Remaining lint and Python dependency findings below |

### Validation commands

```bash
cd backend
HF_HUB_OFFLINE=1 python -m pytest --ignore=tests/test_rag.py --ignore=tests/test_memory_routes.py -q
python -m pip check
cd ../frontend
npm test
npm run lint
npm run build
npm audit --json
```

Backend runs use an isolated Python 3.12 environment; CI must additionally check
its Python 3.11 target. API tests use Mongo doubles, not a real Mongo cluster.
The embedding model was prepared locally and the final full backend run includes
the embedding-dependent tests. Deployment, real MongoDB and browser checks are
reported separately. No external credentials or real publishing were used.

### Dependency findings still open

After compatible frontend fixes, npm audit reports 11 moderate findings and no
high/critical findings. Completing the lint dependency upgrades may require an
ESLint/configuration migration; no forced major upgrade was applied.

The installed-environment Python audit still flags ChromaDB, PyMongo, python-jose,
ecdsa and the Black development tool. It also flags the isolated environment's
pip tool, which is not an application requirement. Some advisories have no listed
fix or require specific unused functionality; applicability remains to be reviewed.
Motor/PyMongo must be migrated together, not independently force-upgraded. This is
not a clean security audit or a declaration that each package is exploitable here.

### Next execution batch

Enforce typed financial auto-approval limits and period caps, complete actionable
pagination, and design the durable state/attempt/outbox boundary before adding
workers or live providers. Then implement the business clock, causal economics,
shared context, outcome memory and measured baseline comparisons.


### Final local validation for batch 1

- `HF_HUB_OFFLINE=1 python -m pytest -q`: **289 passed**, including embedding tests.
- Frontend `npm test`: **21 passed**; `npm run lint` and `npm run build`: passed.
- `python -m pip check`: no broken requirements; multipart 0.0.33 verified in the tested environment.
- `git diff --check`: passed; both Compose YAML files parse.
- Vite reports a large-bundle warning; splitting is future performance work.
- The local backend/frontend start successfully with an empty Groq key and the development in-memory database.
- Playwright browser QA was attempted, but the browser executable was absent and its download returned truncated archives. No browser workflow or mobile/accessibility pass is claimed.
- Real Mongo concurrency, container/Caddy validation, process-kill recovery, backups and live providers remain unverified. No merge, deployment or real provider action was performed.
