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
