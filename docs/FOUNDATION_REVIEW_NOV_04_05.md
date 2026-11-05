# Foundation review — 4–5 November milestones
Reviewed on 5 November 2026 against main 48edae3e6afc2ac87d248b781192f77fa0ae7854.

## Scope and evidence
4 November: business persistence, ownership, account isolation. 5 November: current-code inventory, unresolved backlog and task/approval/event contracts. This is not the later Next.js dashboard, queue, MCP or deployment milestone.
User previously confirmed live local signup/login, account linking, logout and private-page redirect. Atlas health showed connected. This does not by itself prove two-account isolation or restart persistence. Automated evidence below separates doubles, real Mongo and manual/live provider checks. No credentials are requested or stored in this review.

## Actual implementation
|Area|Current source and behaviour|Gap / next task|
|Identity|web/app/actions.ts, web/lib/supabase.ts, backend/app/services/supabase_auth.py: Supabase login, server-only cookies, /auth/v1/user validation; explicit native-session account linking|Manual second-account browser acceptance; provider outage diagnostics; production abuse controls|
|Authorization|backend/app/api/deps.py: user lookup, business owner_user_id checks, task ownership through business; admin role from Mongo|Owner-only tenancy; multi-member membership/RBAC is still T05, not implemented by these tests|
|Next.js|web/app/workspace/page.tsx lists businesses and links accounts|Creation/dashboard/department forms still belong to frontend/ Vite; port 3000 is an additive preview|
|Business records|businesses/profile routes persist in Mongo; auth_identities maps subject to original user_id|Restart proof now has dedicated real-Mongo integration coverage|
|Tasks|services/tasks.py: validated proposals → CEO review → owner/threshold decision → execution claim → ledger/report|No immutable revision IDs/digest-bound approval, durable worker/outbox or deadline scheduler yet|
|Approvals|api/routes/tasks.py performs owner checks and conditional status updates; revision resets CEO authorization|Status comparisons are not full revision compare-and-set. T07/T08 implement revision-bound decisions later|
|Finance|services/ledger.py stores reservations, settlement and simulated ledger; concurrency uses document versions|Period caps, journal growth/reconciliation, causal revenue and payroll remain open|
|Agents|agents/ plus orchestration/registry.py and event_bus.py: Finance, Marketing, HR, Operations, CEO; per-business runtime/snapshots|Only one backend process supported; Strategy is a CEO responsibility, not a sixth/renamed runtime agent|
|Events|orchestration/event_bus.py is in-process, bounded history and sequential callbacks|No durable outbox, sequence recovery or public webhook ingestion contract wired yet|
|Knowledge|rag/store.py + embeddings.py: Chroma similarity retrieval over decisions and local sentence-transformers embeddings|Smart chunks, ACL metadata, lexical fusion, reranking and held-out evaluation still planned|
|External tools|services/social.py + credentials.py: Instagram handler and encrypted tokens|Presence of code is not verified OAuth/publication. Resend/calendar/MCP remain planned|
|Infrastructure|docker/docker-compose.yml and docker-compose.prod.yml, Caddy/Jenkins/Actions files|Next web app not wired into Compose; no staging URL verified; Redis/Kubernetes absent|

## API surface to preserve
/api/auth/register, login, refresh, logout, me and link-supabase; /api/businesses create/list/detail/finances; business-scoped profile, credentials, agents/history, actions, modes, policies, chat, memory, events, tasks, simulation and CEO plans/reports; top-level /api/tasks/{id}/approve, reject, request-changes, revise, assets, ceo-review and release-budget; admin aggregate routes. OpenAPI remains the exact source for methods and payloads. This milestone does not rename or version existing routes.

## Backlog reconciliation
Keep docs/IMPLEMENTATION_CHECKLIST.md and TASKS.md. Historical completed test counts are not a new security audit.
|Existing finding|New plan task(s)|Disposition|
|R01 stale asset/task transition|T07/T08|Existing fix retained; revision binding remains open|
|R02 media validation/storage|T27/T28/T41|Partial image handling exists; restore/live media checks open|
|R03 honest summaries|T32|Existing persisted-outcome summary retained|
|R04 causal economics|T30/T32|Open, needed for measurable simulator claims|
|R05 spend caps|T08/T30|Open; priority before live spending|
|R06 threshold units|T08/T30|Open total-cost enforcement|
|R07 finite scenario limits|T41|Existing validation retained|
|R08 distributed admission|T09/T10/T11|Open; single process remains supported boundary|
|R09 interrupted run recovery|T11|Partial interrupted marking; actual process-kill recovery open|
|R10 durable revision/attempt/outbox|T07–T11|Contract defined here; runtime implementation open|
|R11 unique logical keys/index migration|T07/T09|Required index failures surface; dedupe/migration open|
|R12 shared versioned context|T22–T32|Open|
|R13 measured outcome memory|T33–T37|Open|
|R14 model budgets/concurrency|T39/T41|Bounded in-process request gate exists; distributed budgets open|
|R15 scoped frontend state|T38/T41|Vite guards exist; end-to-end browser checks open|
|R16 onboarding persistence|T38/T41|Existing Vite flow retained|
|R17 pagination|T13/T38|Filtering before limit exists; stable cursor pagination open|
|R18 OAuth/receipts|T18–T29|Open; uncertain side effects must reconcile|
|R19 journal archival|T30/T42|Open; do not silently exceed current journal capacity|
|R20 abuse/key/network controls|T04/T05/T39/T42|Partial; deployment review still required|
|R21 accessibility/responsive UI|T38/T41|Open for full Next migration|
|R22 claims/baselines|T37/T43|Separate plans from implementation; held-out business baselines open|
|R23 dependency review|T40/T41|Open historical findings need fresh applicability review|
|R24 real Mongo/browser/restore/CI|T40–T42|Adds real Mongo CI gate; browser/live provider/backup restore still separate|

## Next implementation order
Finish live two-account and restart acceptance; carry T01 inventory and T02 contracts into 6 November UI work. Then implement immutable task revisions before moving approval/execution to workers. Preserve current business owner IDs and encryption keys. No historical task receives invented requester, approval or completion evidence.

## Manual acceptance on your laptop (still required)
1. Keep your backend and Next.js app running. Sign into the original app account and note the business ID from its API response; note a pending task ID/status if available.
2. Sign out. Create a second app account using another email you control, confirm it, then sign in. This is an app signup, not another Supabase organization/project. The first account's business must not appear.
3. With the second account's session, requesting the original business API URL must return 403. Use your app's request tools; do not paste access tokens in chat. An empty business list alone does not test direct access.
4. Sign back into the original account. Stop the backend using Ctrl+C and start it with your normal command. Refresh/sign in if needed. Confirm the same business ID, owner, pending task ID/status and existing profile data. Check /health reports mongo connected.
5. Record results (no passwords, tokens or connection strings) in the impact log. A failed check stays open; do not create a replacement business to hide missing data.

## Dedicated Mongo test command
CI creates its own disposable MongoDB service. To reproduce locally with Docker, from the project root:
```bash
docker run --rm -d --name simulator-test-mongo -p 127.0.0.1:27018:27017 mongo:7
cd backend
MONGODB_INTEGRATION_URL=mongodb://127.0.0.1:27018 python -m pytest tests/integration/test_mongo_restart.py -q
docker stop simulator-test-mongo
```
Use the backend virtual environment. Environment-variable syntax above is for Git Bash/Linux. This test opens two separate application lifespans and real database connections; it does not kill a process or restart the Mongo server. Supabase identity verification is controlled at the provider boundary; it is not a live Supabase test. It checks persisted identity link, encryption key, ownership, business and pending task plus session revocation across lifespans. The test creates/drops only its random nov45_test_ database and never reads the application .env URI.

## Recorded automated evidence
Commit 2307fa4efb473efe53100c918e81aeab99a5c4ab: [backend CI](https://github.com/syedazoh/STARTUP_SIMULATOR/actions/runs/42050642823) passed all 407 tests in 133.91s, including the real-Mongo linked-account restart test. [Docker CI](https://github.com/syedazoh/STARTUP_SIMULATOR/actions/runs/42050642667) passed HTTP wiring and real backend-container restart persistence/session checks. Local targeted suite: 43 passed; wider offline run: 392 passed, one real-Mongo skip and two embedding-dependent files excluded locally. Remote CI covers those local gaps. Manual acceptance above remains separate from automated evidence.
