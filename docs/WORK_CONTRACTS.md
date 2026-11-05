# Work contracts v1 — foundation design
Status: executable reference schemas in backend/app/models/work_contracts.py, tested but NOT wired into current endpoints, database writes, EventBus or workers. Existing TaskOut/API responses stay unchanged. T02 is contract definition; T07–T14 own rollout/enforcement.

## Boundaries
Use business_id as the tenant key; do not introduce a second tenant_id with a different meaning. Current five runtime departments remain finance/marketing/hr/operations/ceo. Server derives actor_id, business_id and privileges from authenticated context; model validity never grants permission. A user cannot submit an approval record directly to bypass authorization.

## TaskEnvelopeV1
Identity: schema_version=1, task_id, business_id, revision (positive integer).
Purpose: agent, action_type and payload validated using existing ACTION_CONTRACTS, objective and success_criteria.
Origin: kind (manual/chat/ceo_plan/simulation/schedule/webhook/owner_revision), actor_kind (user/agent/system), actor_id and optional source_event_id/parent_task_id/plan_id/run_id.
Control: mode (simulation default/sandbox/live), status, policy_version, priority, created_at and optional due_at as UTC-aware times, bounded unique dependency IDs. Self-dependency is invalid; graph cycles require repository-level checks later. Idempotency key is optional at proposal stage and mandatory before queued execution in T09/T10.
Dates must include timezone and are normalized to UTC. due_at must follow created_at. Defaults from typed action validation are canonicalized before fingerprinting. Unknown fields and NaN/Infinity are rejected. Strings cannot be blank.
The SHA-256 fingerprint covers the complete normalized task record including business, revision, payload/defaults, origin, policy, mode, dependencies and deadlines. It deliberately includes status: approval binds to an immutable proposal snapshot, not the mutable execution record. Store that snapshot/digest separately during T07. Do not recompute it from a status-mutated task and assume it represents an approved proposal.

## ApprovalRecordV1
approval_id, business_id, task_id, revision, task_digest (64 lowercase hex), stage (ceo/owner/policy), decision (approve/reject/request_changes/escalate), decided_by, reason, policy_version, decided_at and expires_at. Expiry must follow decision time. Actor role, scope, policy eligibility and the match against current task revision MUST be checked by future services, not trusted from this object. Owner authority remains separate from CEO recommendation and Finance reservation.

## DomainEventV1
schema_version=1, event_id, business_id, task_id, revision, monotonically assigned per-business sequence, event_type, actor_id, correlation_id, occurred_at and optional causation_id/evidence_ref. Only allowlisted task/approval events. Carries identifiers rather than arbitrary tool payloads, secrets, candidate records or email bodies. Consumers fetch authorized task details; reconnect replays sequence through a scoped API later. Schema does not allocate sequence or deliver events.

## State transition design
|From|Allowed next states|Guard|
|draft|pending_ceo_review, cancelled|Valid typed proposal, actor and business ownership|
|pending_ceo_review / ceo_reviewing|pending_approval, awaiting_asset, needs_revision, rejected|CEO review result bound to revision; lease for concurrent reviews|
|pending_approval|approved, rejected, needs_changes, expired, cancelled|Authorized human or bounded policy; current unexpired revision|
|approved / auto_approved|queued, expired, cancelled|Dependencies satisfied; approval valid; reserve funds|
|queued|executing, cancelled, expired|Atomic claim, valid lease and idempotency record|
|executing|awaiting_external, executed, failed, denied, reconciliation_required|Persist effect evidence; unknown provider outcome never blindly retries|
|awaiting_external|executed, failed, reconciliation_required|Verified receipt or bounded reconciliation|
|executed|verified_complete|Business success criteria plus evidence review|
|needs_changes / needs_revision|pending_ceo_review, cancelled|New immutable revision; earlier approvals invalidated|
Unknown-outcome reconciliation is an operator workflow, not a generic transition back to queued. Entire dependency graph, expiry-at-execution and permissions require T07–T12 runtime services. Lifecycle describes target behaviour, not implemented enforcement.

## Future API commands (design, not live endpoints)
Propose: typed action + objective + deadline + idempotency key; server supplies origin actor/tenant. Revise: expected_revision plus changed proposal; conflict 409 for stale version. Decide: expected_revision, proposal_digest, decision, reason; server supplies approver. Event read: after_sequence + bounded limit; require membership. Retain existing detail error responses until a deliberate migration; 401 unauthenticated, 403 wrong owner, 404 absent, 409 stale/conflicting, 422 invalid payload, 503 dependency unavailable.

## Idempotency and rollout
Store unique (business_id, command_scope, idempotency_key) with request digest and result; same key+same body replays result, same key+different body is 409, in-flight duplicate is explicit 409. Keys must survive retries/replays. Create task version, approval, outbox and reservations atomically where invariants require it; Mongo transactions need replica-set testing. Workers recheck authority and classify uncertain outcomes. Redis Pub/Sub cannot replace the durable outbox.
Backfill existing tasks with an explicit legacy marker and unknown provenance where necessary; never fabricate origin or grandfather unknown live approvals. Dry-run counts, backup, rollout flag and rollback are prerequisites. Keep JSON payload fields additive until all consumers migrate. Contract instances are not signed credentials or authorization tokens.
