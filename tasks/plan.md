# Implementation plan
Planning deliverable only. See docs/PRD.md for scope, docs/WORKFLOWS.md for business procedures, docs/architecture.md for system design and tasks/todo.md for ordered work.

## Delivery order
1. Establish contracts, identity and tenant isolation.
2. Deliver one approved email task end to end with durable execution and evidence.
3. Add MCP gateway and calendar; complete HR hiring demonstration with human decisions.
4. Complete Marketing organic post, Finance simulated ledger and Operations deadline flows.
5. Add CEO evidence summaries and evaluate improved RAG.
6. Finish Next.js migration, reliability testing and staged deployment.
Next.js can be developed alongside existing frontend behind routing/feature flags; preserve working API compatibility. Do not change frontend, authentication, database and all agent behaviours in one release.

## Cutover and rollback
Map existing users to verified Supabase identities; test ownership mapping before cutover; do not link accounts solely by unverified email. Define old session expiry and recovery instructions. Backfill task source/version/approval fields; legacy pending actions require review when provenance is insufficient. Keep old frontend available during staged rollout. Back up and test schema migration rollback; never rewrite production records without dry-run counts and validation.

## Release gates
Auth/tenant tests; immutable approvals; duplicate/reordered webhook tests; job crash/restart; external success followed by persistence failure; calendar timezone/conflict; disconnected provider; overdue task escalation; grounded RAG citations; responsive/keyboard UI; backup restore. Test business logic without paid providers, then sandbox contracts, then controlled live acceptance only with authorization.

## Risks and decisions
Provider permissions may delay live integrations: implement explicit sandbox adapters. Scope can exceed FYP capacity: demonstrate five complete representative workflows and defer paid ads/payment/Kubernetes. MongoDB and Supabase add operational complexity: initially use Supabase only for identity. Dates, budget, team capacity and target hosting remain open; estimates require those inputs. No fine-tuning or enterprise-scale claim before evaluation demonstrates need.

## Later roadmap
Paid ads, accounting/payment integrations, richer ATS/CRM, independent microservices, Kubernetes and model fine-tuning each require a separate measured problem, specification, cost and acceptance gate.

## Existing backlog preservation
Read docs/IMPLEMENTATION_CHECKLIST.md before implementation. Its unfinished R01–R24 findings remain active; map them to these tasks during T01 and preserve their evidence. TASKS.md is historical change history, not this new task list. Existing code/tests determine current behaviour; these proposed milestones do not imply features are absent or complete.

## Additive dataset simulation — November 10, 2026
User-authorized scope: one synthetic product-launch scenario. Preserve the broader unfinished plan above.
1. Versioned schema, sample JSON/CSV and data dictionary.
2. Atomic snapshot importer with preview, duplicate protection and owner isolation.
3. Deterministic five-department review, existing owner approval/execution integration, metrics and baseline.
4. Next.js demo workspace, evidence inspection and archival reset.
5. Focused/broader regression checks, local-fixture browser acceptance and documentation.
Design and verification boundaries: docs/DATASET_SIMULATION.md. No production deployment or changes to real financial state.

## FYP submission execution — 24–30 November 2026

This extends the same unfinished project plan; it does not replace earlier unchecked requirements. Main baseline: d9e4b03 on 24 November. Submission target: 30 November. Accepted technical brief: the uploaded 24 November instructions; the accidental word before Persistent storage is ignored. No proposal PDF is present in the checkout, so proposal quotations/approval remain unverified. Preserve existing five agents and add distinct Support/Strategy workflows without renaming departments. Existing approved purple/glass presentation is retained during engineering; the brief's historical Emerald naming conflicts with current DESIGN.md and is recorded rather than triggering an unrelated redesign.

Critical path and realistic dates (targets, not completion claims):
- **24 Nov / P0:** reproduce web-only clean-install failure; repair host dependency ownership; run unit/types/build/start/browser gates. Baseline clean web install/tests pass, production build fails resolving three from shared frontend landing; backend baseline initially blocked by missing pytest in this execution environment.
- **25–26 Nov / P1:** versioned business-scoped role-work contract, actual independent role workers using a durable queue; claims/fencing/retries/crash/cancel tests. Add Support ticket drafts/escalation and Strategy scenario recommendations as distinct read-only roles; retain one existing approval/ledger execution authority. Verify a real Mongo + cross-process scenario, not duplicated registries.
- **27 Nov / P2:** expose artifacts/progress and safely downloadable JSON/CSV evidence; connect authorized retrieval/context and record rule/AI modes. Verify revisions change the proposal or explicitly block.
- **28 Nov / P3:** select Next release packaging, private Compose topology, worker/API readiness/storage/recovery, Jenkins build/test path and rollback/operator instructions. Local images/smokes do not prove AWS/Jenkins execution.
- **29–30 Nov / P4:** bounded seven-role scenario, baseline/comparison evaluation with honest model modes, resource/latency measurements, production browser rehearsal and final matrix/CI review.

Each slice requires expected behavior, focused tests, diff/security review, corrections, integration evidence and its own commit. One slice must be accepted before expanding. Keep external Gmail/Meta/calendar extensions below core simulation/distribution/evaluation. No external communication, paid resources or deployment is authorized. Production provider keys, proposal PDF, Jenkins controller and AWS account access remain operator dependencies; continue independent local work while these are absent. Full live delivery and cloud/Jenkins proof cannot be guaranteed by 30 November without those inputs. Any missed gate remains partial/blocked, not silently removed.

## Shared five-agent conversation and realistic retail evaluation — 27 November 2026
Extends the existing project and preserves all earlier unfinished work. User now explicitly requests CEO, Finance, Marketing, Operations and Strategy; retain legacy HR records/routes, but the shared launch workflow uses Strategy and Operations covers staffing recommendations. Native password login stays active. ZIPs contain only screenshot references (navigation patterns and glass dashboards), not execution instructions. No billing/payments feature follows from the billing screenshot.

Implementation slices, in dependency order:
1. Retail data: strict signed-quantity GBP CSV/JSON preview/import, structured totals/demand/returns and provenance; no currency mixing or mutation of the simulated ledger. Verify Decimal totals, cancellation handling, duplicates and tenant denial. Official UCI host currently blocked (403); source rows cannot be claimed downloaded until access is granted.
2. Role/context contract: shared role configuration, authorized records plus existing retrieval, bounded structured recommendations and scoped references. Preserve HR compatibility. Verify all five roles, clarification, missing facts, unrelated requests and prompt-injection boundaries.
3. Conversation persistence: idempotent turns and immutable recommendation artifacts, explicit follow-up reference resolution, short speech text; no task execution from conversation. Verify retries/concurrency/foreign references.
4. Launch assignments: existing CEO plans and task pipeline gain internal brief assignments; separate owner activation, immutable submissions, review/request-changes and renewed exact approval. Verify four child tasks, linked submissions and prior-version retention.
5. Shared image tool: existing durable jobs + validated stored image artifacts, provider adapter, authorized preview/download, revision parent and failed-job retry. Verify Marketing and Strategy, duplicate jobs, failures and tenant isolation with mocks; live provider is unconfigured.
6. Shared React conversation/voice: one component in all personal workspaces and boardrooms in both apps, explicit microphone finish/review/send, interrupt/Stop, stale-audio cleanup and typed fallback. Adopt useful sidebar/glass reference patterns, retain themes/accessibility and existing avatars.
7. Demo/evaluation: one clearly synthetic startup with goals/catalog/budget/brand/deadlines/capacity; eight short examples per role, six development plus two held-out per role. Reproducible current-model evaluation and mock-labelled reports; do not fine-tune without measured persistent failure.
8. Final checks: focused and broad backend gates, builds/lint/types, desktop/mobile browser flows, no duplicate effects or cross-business data, demo guide, DATA_SOURCES.md and explicit live/configuration limitations. Do not deploy or publish environment.
Each slice is committed only after its focused checks; shared schema/API changes precede UI wiring. No authentication migration, duplicate queue, real social post, email, hiring or spending is authorized by generated content. Existing owner-approved task execution remains authoritative.
