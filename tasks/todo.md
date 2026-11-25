# Implementation tasks
Progress is recorded with evidence below. Unchecked items remain planned. Each item must be split further if implementation exceeds about five files.

## Foundation
### T01: Inventory routes, schemas, providers and existing tests
- [x] Review current implementation, ownership boundaries and provider/test coverage.
- [x] Map all R01–R24 findings to the implementation backlog without removing unfinished work.
Evidence: docs/FOUNDATION_REVIEW_NOV_04_05.md; baseline main commit recorded there. Existing authentication UI is an additive preview, not the completed dashboard.

### T02: Create task/event/approval contracts
- [x] Define and test versioned task, approval and domain event reference schemas.
- [x] Document provenance, deadlines, proposal fingerprints, approval scope/expiry, state transition guards and idempotency.
- [x] Preserve current endpoints; explicitly separate reference design from runtime adoption.
Evidence: backend/app/models/work_contracts.py, backend/tests/test_work_contracts.py and docs/WORK_CONTRACTS.md. Runtime persistence/enforcement stays in T07–T14; T02 completion does not imply those tasks are complete.

### T03: Bootstrap Next.js login shell
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T02; reuse earlier foundation contracts.
Likely area: frontend/ and backend/app/api/; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T04: Integrate Supabase identity verification
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T03; reuse earlier foundation contracts.
Likely area: frontend/ and backend/app/api/; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T05: Enforce tenant memberships and roles
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T04; reuse earlier foundation contracts.
Likely area: frontend/ and backend/app/api/; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T06: Migrate existing login identities safely
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T05; reuse earlier foundation contracts.
Likely area: frontend/ and backend/app/api/; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

- [ ] Phase checkpoint: demonstrate completed behaviour, review unresolved risks, verify documentation and rollback.

## Reliable work
### T07: Implement immutable task versions
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T06; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T08: Implement human approval binding and expiry
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T07; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T09: Add transactional outbox and webhook inbox
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T08; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T10: Configure Redis worker and idempotent execution
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T09; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T11: Add leases retries and reconciliation
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T10; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T12: Add deadline scheduler and escalation
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T11; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T13: Build task detail and approval inbox
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T12; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T14: Add Socket.IO auth rooms and reconnect recovery
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T13; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

- [ ] Phase checkpoint: demonstrate completed behaviour, review unresolved risks, verify documentation and rollback.

## Tools
### T15: Implement MCP server auth and schemas
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T14; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T16: Implement MCP read tools
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T15; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T17: Implement approved action tool gateway
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T16; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T18: Implement Resend send and delivery callbacks
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T17; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T19: Implement inbound email correlation
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T18; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T20: Implement calendar OAuth and freebusy
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T19; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T21: Implement calendar scheduling and cancellation
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T20; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

- [ ] Phase checkpoint: demonstrate completed behaviour, review unresolved risks, verify documentation and rollback.

## Departments
### T22: Build HR requisition and budget checks
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T21; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T23: Build applicant intake and access control
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T22; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T24: Build human-reviewed shortlist
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T23; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T25: Build interview scheduling workflow
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T24; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T26: Build offer draft and onboarding workflow
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T25; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T27: Build Marketing briefs and asset review
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T26; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T28: Build one organic publishing adapter
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T27; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T29: Build publication verification and metrics
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T28; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T30: Build Finance reservations and ledger reconciliation
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T29; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T31: Build Operations milestones and dependencies
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T30; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T32: Build CEO evidence projection and summary
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T31; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

- [ ] Phase checkpoint: demonstrate completed behaviour, review unresolved risks, verify documentation and rollback.

## Knowledge
### T33: Build document parsing and access metadata
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T32; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T34: Implement smart versioned chunking
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T33; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T35: Add lexical and dense retrieval fusion
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T34; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T36: Add reranking and grounded citation output
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T35; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T37: Create held-out RAG evaluation and freshness tests
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T36; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

- [ ] Phase checkpoint: demonstrate completed behaviour, review unresolved risks, verify documentation and rollback.

## Release
### T38: Port remaining frontend routes and accessible boardroom
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T37; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T39: Add tracing logs metrics and cost limits
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T38; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T40: Implement CI and staging release checks
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T39; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T41: Run cross-tenant and failure recovery suite
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T40; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T42: Run load baseline and backup restore
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T41; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T43: Prepare FYP demo evidence and manual guide
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T42; reuse earlier foundation contracts.
Likely area: backend/app/ and corresponding frontend feature/tests; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

- [ ] Phase checkpoint: demonstrate completed behaviour, review unresolved risks, verify documentation and rollback.

## Existing backlog preservation
Read docs/IMPLEMENTATION_CHECKLIST.md before implementation. Its unfinished R01–R24 findings remain active; map them to these tasks during T01 and preserve their evidence. TASKS.md is historical change history, not this new task list. Existing code/tests determine current behaviour; these proposed milestones do not imply features are absent or complete.

## Authentication migration progress — 3 November 2026
T03/T04/T06: initial additive Next.js/Supabase flow and explicit existing-account linking implemented. Full tasks remain unchecked pending live provider validation, frontend migration and real Atlas acceptance. Owner-only isolation reused; multi-member roles (T05) remain planned. See docs/SUPABASE_AUTH_SETUP.md for setup and test boundaries.

## 4–5 November 2026 foundation verification
- [x] Add two-owner API isolation tests: private business lists, forbidden cross-owner reads/task mutations, ignored forged owner IDs, invalid sessions.
- [x] Add real-Mongo application-lifespan restart test and MongoDB CI service; random isolated database with cleanup, no application .env database used.
- [x] Real-Mongo CI passed: backend run 42050642823, 407 tests passed including the restart test; Docker run 42050642667 passed real container restart/session/snapshot checks.
- [ ] Manual browser acceptance: sign in with a second registered email; original business must not appear and copied original business API URL must be forbidden. Sign back into original account.
- [ ] Manual local restart: note original business/task IDs, restart backend, sign in again and confirm IDs/status are preserved on Atlas.
Full multi-member RBAC, abrupt process termination recovery, provider acceptance and deployment remain separate milestones.

## Dataset-driven simulation — additive work, November 10, 2026
These checks do not mark any November 4+ daily milestone complete or close the broader T07–T43 roadmap.
- [x] DS01: Define bounded synthetic-only schema, globally unique record IDs, relationships, sample JSON/CSV and data dictionary.
- [x] DS02: Add owner-scoped preview/commit importer; atomic snapshot, deterministic duplicate keys, row/field validation and cross-business denial tests.
- [x] DS03: Use shared structured records and department-filtered reference citations across five deterministic department adapters.
- [x] DS04: Run one immutable simulated launch through existing task approvals; retain result, baseline, rule version and evidence. Test stale, expired, rejected and repeated decisions.
- [x] DS05: Add Next.js demo dashboard, explicit simulation labels, preview/confirm import and scoped archival reset.
- [x] DS06: Run focused tests, fixed baseline evaluation and local-fixture browser acceptance; document results and limitations in docs/impact.md.
- [ ] DS07: Verify the new flow against configured live Supabase and real MongoDB restart persistence; not established by doubles/local identity fixtures.
Evidence and acceptance instructions: docs/DATASET_SIMULATION.md; datasets/product-launch-v1/. Regular agents remain unchanged; demo adapters are not represented as live LLM decisions.

## Purple 3D executive studio — November 17, 2026
- [x] Implement user-directed black/purple identity with warm beige/off-white across the Next.js workspace and existing Vite surfaces.
- [x] Add an authenticated Next.js executive studio reusing existing ownership, tasks, agent snapshots and approval routes.
- [x] Share real procedural 3D avatars/workstations, task packets and event/task state mapping without React renderer-version mixing.
- [x] Separate owner authorization from CEO review, avoid historical replay, and label the non-mutating visual preview.
- [x] Add immersive/follow controls, reduced motion, accessible list view, camera reset and responsive label placement.
- [x] Run frontend behavioral checks, builds/typecheck, local-fixture browser acceptance and a separate visual review; record limits in docs/impact.md.
- [ ] Verify the redesigned flow on the user's configured Supabase/backend/business and target hardware. Direct HelloRun/Figma comparison remains unavailable until those sources are accessible.
These checks do not close unrelated November roadmap milestones, backend worker/realtime work or live-provider acceptance.

## November 16 — Next.js command-center slice and November 30 target
- [x] Reuse the existing dataset import/approved-launch demo on main; do not rebuild it.
- [x] Add Next.js business creation and business-specific command-center navigation.
- [x] Connect department state/proposals, CEO draft review/activation, internal owner decisions, finance summary and saved reports to existing authorized APIs.
- [x] Show source/plan/CEO/owner/result distinctions and partial errors; keep unknown deadlines explicit.
- [x] Add opt-in atomic approval-preview binding and cross-owner/stale/concurrent-edit regression checks.
- [x] Record passing Next.js production browser/build, backend and Docker CI evidence in docs/impact.md (November 16). Display follow-up has its own checks.
- [ ] User acceptance on local Atlas/Supabase after pulling (docs/NEXT_COMMAND_CENTER.md).
Full T07/T08 versioning, worker/outbox/MCP, deadline scheduler, advanced RAG, complete frontend migration and deployment remain unchecked. Revised submission target is November 30; the old December 5 plan is superseded for submission. No staged deployment URL has been verified by this slice.

## November 16 — Reported Vite dashboard/revision fixes
- [x] Trace counter flicker to loading gates during polling; preserve last confirmed snapshots and suppress overlapping requests.
- [x] Keep request-changes task visible and implement feedback-driven typed revision with an explicit blocked state for unavailable/unchanged output.
- [x] Require a fresh owner approval after revision, including in auto mode; keep unchanged work blocked and concurrent rejection authoritative.
- [x] Record passing backend, Next/Vite browser, frontend and Docker CI evidence in docs/impact.md; live local/provider acceptance remains separate.
The remaining submission work is unchanged: durable jobs/outbox/MCP, advanced RAG, deadlines, deployment and live acceptance. These fixes do not mark the entire plan complete.


## November 17 — jobs, deadlines, MCP and document knowledge
- [x] Durable Mongo queue/atomic claims, bounded retries, task-outbox repair and optional Redis hints.
- [x] Internal approved execution only; uncertain effects require reconciliation; preserve synchronous compatibility.
- [x] Versioned UTC deadlines, in-app reminder/overdue/CEO-owner escalation and common execution cutoff.
- [x] Official private stateless MCP with revocable tenant/department access and proposal-only writes.
- [x] Markdown/text knowledge ingestion, smart chunks/metadata, hybrid retrieval, cached reranking, strict prompt, version-aware citations/abstention and explicit fallbacks.
- [x] Next automation controls, README setup, model/client scripts, synthetic retrieval fixture and automated acceptance coverage.
- [ ] User acceptance with local Atlas/Supabase and representative documents.
- [ ] Production domain, HTTPS/MCP routing, provider integrations, staging/deployment and backup/monitoring acceptance.
Implementation above supersedes the earlier November 16 entries that listed these features as future work. Full distributed services, PDF/OCR and general autonomous external actions remain outside this slice. Check docs/impact.md for executed verification, rather than interpreting this list as deployed proof.

- [x] Make boardroom task transfers visibly directional with bright lines, arrowheads, document packets and readable route cards; queue every observed assignment and demonstrate CEO → Finance budget delegation using disposable browser fixtures.

- [x] Extend collaboration visuals to all five executives: sender/receiver participant roles, full launch-meeting preview, every new routed event in snapshot order, and regression coverage for all twenty explicit department pairs.

- [x] Connect decision-log observations and task states to both boardroom timelines; add selected-avatar-only scene filtering and restore full room on All events. Apply readable text sizes across both apps and verify mobile wrapping, backend history isolation and decision-driven signals.

- [x] Replace both public homepages with a shared glass/3D landing, device-aware persisted theme toggle, five English narrated/captioned agent introductions, playback controls, sliding profile, native overview popup and phone/reduced-motion/fallback behavior. Preserve account routes and authenticated themes.

- [x] Add a captioned product walkthrough video, setup/workspace replay links, transcript/checklist and lazy native playback in both frontends; validate byte-range serving, mobile layout and public-only media caching.
- [x] Record selected integration priorities (Gmail, Instagram and Facebook), current adapter gaps, AWS frontend/container decision and measurable staging latency targets in docs/RELEASE_ROADMAP.md.
- [ ] Implement and verify Gmail OAuth/token lifecycle and approved email execution with controlled delivery receipts.
- [ ] Complete Instagram/Facebook OAuth/account eligibility, media publishing and verified provider receipts before live automation.
- [ ] Resolve production frontend packaging, provider permission acceptance, AWS staging, load/latency baselines and rollback before production deployment.

- [x] Diagnose local Vite auth proxy refusal, document required FastAPI startup, improve proxy/missing-config feedback, correct Next immediate-session signup and preserve explicit legacy account linking. Add local setup diagnostics and auth regression/browser checks.

## FYP submission execution — 24 November 2026
Preserve the earlier unfinished backlog. Dependency/dates: tasks/plan.md; evidence: docs/FYP_IMPLEMENTATION_MATRIX.md.
- [x] P0 Clean web-only build, dependency-boundary regression and production browser acceptance (local/container; remote CI lookup remains pending).
- [x] P1 Independent role workers with durable versioned messages and real-process recovery/tenant/idempotency tests (also ten-service local container acceptance).
- [ ] P1 Distinct Support and Strategy workflows without renaming five existing departments.
- [ ] P2 Saved content/grounded drafts, owner revisions and tenant-safe CSV/JSON evidence download.
- [ ] P2 Complete bounded seven-role scenario with persisted outcomes/reports and actual output modes.
- [ ] P3 Next production image/Compose, Jenkins alignment, private networking/storage and recovery smoke.
- [ ] P4 Fresh workflow/retrieval/output/latency/resource evaluation, integrated browser rehearsal and final CI evidence.

- [x] P0 build slice: reproduced/fixed web-only Three resolution; 27 tests/types/build/start, production workspace fixture browser and landing 3D/fallback; Vite 62 tests/lint/build. Remote CI lookup blocked (Forbidden).

- [x] P1 initial distributed slice: seven actual role processes, versioned scoped messages, claim/retry/fence/poison/deadline/cancel tests, Support/Strategy artifacts, existing campaign approval/execution integration (29 focused checks passed).
- [ ] P1 follow-up: current staffing/capacity services, richer arbitration and dashboard exposure; full seven-role/AI quality acceptance remains partial.

- [x] P2 dashboard/export slice: seven saved worker queues/artifacts/citations and existing owner-review path exposed in Next; bounded tenant-authorized CSV/JSON downloads with secret allowlist and formula protection. 22 focused backend checks, 27 web checks/types/build and production fixture browser flow passed.
- [ ] P2 acceptance remains partial: model-assisted Marketing/Support artifacts and comparable labelled AI-vs-rule output evaluation.

- [x] P3 local packaging slice: Next standalone/nonced CSP, minimal role-worker image, restricted authenticated Mongo, private ten-service workflow through owner execution, health checks, Mongo restore, Jenkins source path and operator runbook validated locally.
- [ ] P3 release acceptance: Jenkins controller run, production-volume restore, real HTTPS/Supabase and authorized AWS rollout. Cached-model tests/hybrid evaluation are verified.

- [x] P1 correctness follow-up: saved HR/Operations context, validated predecessor results, delayed coordinator recovery and late-result rejection; 14 focused/real-process tests and restricted snapshot-read/write checks passed.

- [x] P4 regression repair: empty/saved Chroma history works without model loading; semantic search remains explicit when unavailable, memory reads are bounded/non-blocking and tenant errors are preserved (5 focused checks passed). Model-backed retrieval subsequently passed 50/50 with the approved model cache.

- [x] P4 local evaluation: four held-out rule/output cases, real primary scenario, 100 concurrency-four protected reads, cold topology startup and complete ten-container snapshot; actual evidence/modes/limitations saved.
- [ ] Remaining release gates: actual AI-assisted outputs/comparison, proposal PDF mapping, Jenkins controller, real HTTPS/Supabase/volume recovery and authorized AWS rollout. Cached-model validation now passes 504/504 tests and 50/50 hybrid retrieval.

- [x] Final main/CI evidence: native main push verified through b999c6e; official GitHub web pages show Frontend, Next, Docker wiring and Backend workflows successful, with configured backend hybrid/model gates.
- [x] Apply approved model-access hosts: observed revision 9, public downloads and offline model-cache validation passed. Assistant did not publish the environment. Real AI-generated output/comparison remains a separate open gate.

- [x] Approved host grant active (observed revision 9); public models downloaded without token; offline real-Mongo container suite 504/504 and required hybrid retrieval 50/50 passed. Earlier nine local cache failures resolved.
- [x] Repair container test fixture wiring: read-only datasets/diagnostic mounts in Jenkins/Compose; provider key forced empty and memory/uploads isolated in the test profile. Existing assertions retained.
- [ ] Remaining: actual new AI-generated artifact/comparison acceptance, proposal PDF mapping, real Jenkins controller, HTTPS/Supabase, production-volume recovery and authorized AWS deployment.

- [x] Container fixture follow-up e750dd8: GitHub Docker Compose Wiring completed successfully; evidence: docs/evaluation/ci-e750dd8.json.

## Cinematic landing — 24 November 2026
- [x] Phase 1: public cinematic hero/3D, sticky navigation, persistent motion preference/OS override, existing captioned-demo entry and Free/Planned presentation shared by Next and Vite.
- [x] Verify Next types/27 tests/build; Vite lint/63 tests/build; Chromium five-width dark/light and preference/demo/dialog/3D-storage-voice fallback checks. Evidence: docs/design/CINEMATIC_LANDING_PHASE_1.md.
- [x] Phase 2: Skiper legacy expanded agent chapters, Vengence text reveal and nine-step synthetic launch handoffs with Framer Motion; five departments plus separate owner, manual/playback controls and motion/fallback handling. Evidence: docs/design/CINEMATIC_LANDING_PHASE_2.md.
- [ ] Define paid plan names, prices, quotas and entitlements before subscription implementation. No billing claim from landing presentation.
- [ ] Later: actual-device/browser and performance verification; existing Vite bundle-size concern remains.

## Landing correction — 24 November 2026
- [x] Remove owner-rejected public messaging walkthrough, its unused module/styles and obsolete tests; retain authenticated communication features.
- [x] Poster and explicit video button play the real project recording in a modal; separate written guide, captions, native playback/fullscreen, Escape pause and error recovery.
- [x] Add scoped metallic Three.js background with reduced-motion/WebGL fallback; retain existing themes and agent introductions.
- [x] Dashboard references received and adapted: Next compact sidebar/KPI/chart/attention overview and Vite history-first dashboard in the existing black/purple/beige theme. Existing data/actions preserved; see docs/design/DASHBOARD_REFERENCE_UPDATE.md.
Evidence: docs/design/LANDING_VIDEO_CORRECTION.md.

- [x] Dashboard verification: Next local fake-provider route/approval check and five widths; Vite isolated API/history five widths; 90 existing unit tests, applicable lint/types/builds. No real account or provider side effects.


## Agent workspace recovery — 24 November 2026
- [x] Restore dedicated Next CEO/Finance/Marketing/HR/Operations routes and working navigation.
- [x] Reuse scoped chat/history, department mode/policy and existing proposal/approval services; validate writes and guard repeated submits.
- [x] Explain original Supabase identity versus native account and Mongo business records; distinguish account-link failures.
- [x] Make sidebars scroll, add small role avatars, persistent pausable backgrounds and complete public/private footers; repair mobile task controls.
- [ ] Complete Next parity for classic Marketing publishing/media/connected-account controls. Keep existing Vite screens available meanwhile.
- [ ] Validate the owner's actual original Mongo database/account link locally using private configuration; disposable fixtures do not prove this connection.

## Coordinated appearance and team setup — 24 November 2026
- [x] Add validated owner-reported workforce storage, creation compatibility, tenant-scoped editing and distinct chat context; 25 focused offline backend tests passed.
- [x] Finish shared appearance presets, avatar-free beige footer sculpture, dashboard role links and team setup in both frontends; verify 97 frontend tests, builds/types/lint, browser variants/video/profile and Docker packaging.
- [ ] Owner validates original Supabase/Mongo business access locally, then completes the presentation acceptance and authorized AWS deployment (docs/RELEASE_PLAN_2026_11.md).

- [x] Keep explicit light/dark toggle plus Appearance on every UI route, including after scroll/navigation and inside immersive boardroom; cover guide/setup/admin theme surfaces and keyboard access. Next 16-route disposable acceptance and classic agent/profile checks passed.

## 25 November 2026 — access and contextual demo
- [x] Canonical same-screen existing-user Supabase code login, protected return, explicit password fallback and verified same-host classic restoration; both-session logout. Preserve original ownership linking.
- [x] Shared scoped conversation rules; deterministic clarification/definition/task queries; bounded authorized context for model answers and source labels.
- [x] Five retained roles including HR; shared saved what/why/decision, English narration/Stop/text fallback.
- [x] Marketing two-caption recommendation → Finance ledger evidence → owner-recorded CEO review/revision/rejection → one internal draft task through existing plan/task approvals, including concurrency/lost-response retry.
- [x] Emerald/Champagne/Lavender on shared surfaces; real scoped donut/workload/backing table; dated-only trends.
- [x] Local fixture-backed browser journey and focused tests; guide and actual deterministic/mock response evidence in docs/NOV25_DELIVERY_REPORT.md.
- [ ] Operator verification of original Supabase email delivery, original Mongo business/link and live model inference using private configuration. No deployment inferred from local tests.
