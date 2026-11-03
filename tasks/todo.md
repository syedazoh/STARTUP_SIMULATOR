# Implementation tasks
All tasks are proposed and unchecked. Suggested sequence; no completion dates are assumed. Each item must be split further if implementation exceeds about five files.

## Foundation
### T01: Inventory routes, schemas, providers and existing tests
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: baseline repository inspection.
Likely area: frontend/ and backend/app/api/; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

### T02: Create task/event/approval contracts
- [ ] Implement and document this capability through its API and UI/worker path where relevant.
- [ ] Acceptance: normal case succeeds with persisted evidence; unauthorized/invalid case fails without side effects; retry/reload preserves consistent state.
- [ ] Verification: focused backend or frontend tests plus applicable build/type checks; record actual commands and results in docs/impact.md. Integration tasks also require sandbox provider contract tests.
Dependencies: T01; reuse earlier foundation contracts.
Likely area: frontend/ and backend/app/api/; identify exact files during preflight. Scope: S/M target, subdivide before changes if larger.

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
