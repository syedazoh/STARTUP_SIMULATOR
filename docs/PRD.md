# Startup Simulator — Product requirements
Status: proposed plan, 3 November 2026. No implementation or external action is claimed.

## Objective and scope
Build a supervised startup operating workspace with CEO, Finance, HR, Marketing and Operations agents. Users set objectives, budgets, deadlines and permissions; agents propose and perform bounded work through tools; users see evidence of outcomes. Keep simulation, sandbox and live execution visibly separate. A simulation must never silently become a real email, hire, advertisement or payment.

“All startup tasks” is a long-term capability map, not a claim that five agents replace all professional judgment. The FYP demonstrates complete representative workflows across all five departments. Legal advice, tax filing, payroll payments, banking, contract signatures and autonomous hiring decisions remain human-controlled or explicitly simulated.

## Current evidence
Earlier code inspection of main at 21e615c1dfa277804856cf34d164e9d4ec7093bf found FastAPI, MongoDB/Motor, LangGraph, Groq, Chroma, local embeddings, a custom EventBus and a CEO/owner task approval pipeline. tasks.py has real Instagram action handlers. Those handlers have not been live-tested in this review. No MCP implementation was found in inspected paths/dependencies. Current frontend is React/Vite; Next.js is a proposed migration. This document does not imply a fresh full audit or test run.

## User journey
1. Register, verify email, sign in and create a business workspace.
2. Set company profile, timezone, operating hours, budget, team membership and agent responsibilities.
3. Choose simulation/sandbox/live mode. Connect integrations with separate scopes and test status.
4. Upload approved policies, business plans, brand guidance and department documents.
5. Set an objective such as “hire one designer by 30 November” or “prepare next week's campaign”.
6. CEO creates a visible plan with child tasks, dependencies, owners, cost estimates and deadlines.
7. Departments propose actions. The approval inbox shows exact recipients/content/cost/target account, reasons, source trigger and consequences.
8. Owner approves, rejects, edits or requests revision. Workers execute eligible actions.
9. Timeline shows provider receipts, meetings, documents and errors. CEO summarizes verified outcomes and exceptions.
10. User resolves blockers, reviews results and closes or revises the objective.

## Task origins and approvals
A task can originate from a direct user request, scheduled policy, signed webhook, departmental proposal or CEO delegation. Every origin stores the actor, source event, original request, parent objective and timestamps. External text is data, never authorization.
CEO review assesses alignment, dependencies and policy. Owner or designated human approval authorizes sensitive actions. Finance reserves funds separately. Agent reasoning is never a substitute for permission.
Read-only queries may run within granted scope. Internal drafts may be automatic. Sending externally, publishing, offers, paid ads and purchases require explicit approval by default. A workspace owner may later grant bounded recurring authority with destination, content class, spend cap and expiry. Final hiring/rejection decisions remain human decisions.
Approval binds to an immutable action version: payload hash, recipients, provider account, cost/currency, policy version and expiry. Any material edit invalidates approval. A pending task displays “requested by”, “reviewed by”, “waiting for”, “why approval is required”, and “approval expires”. CEO cannot approve its own privileged external action.

## Common lifecycle
Draft → proposed → validating → CEO review → awaiting human approval → approved → queued → running → awaiting external outcome → verified complete.
Alternate states: needs revision, rejected, blocked, cancelled, expired, retry scheduled, failed, reconciliation required. Transitions require authorization and optimistic concurrency. Pending approval is never executable. Provider acceptance is not business completion.
Each task stores tenant_id, id, objective_id, parent_id, actor, department, origin, action schema/version, immutable payload, mode, priority, due_at UTC, display timezone, dependency IDs, approval IDs, idempotency key, attempts, lease, cost reservation, external IDs, evidence, error classification and audit timestamps.
A scheduler sends configurable reminders, flags overdue work and escalates blockers. Moving a deadline requires a recorded reason. Workers must not run cancelled/expired versions.

## Department capability map
|Agent|FYP working capability|Later extension|Human boundary|
|CEO|Plan, delegate, review, summarize, escalate|Forecast portfolios and compare scenarios|Owner controls authority and strategic commitments|
|HR|Job brief, applicant intake, consent, interview scheduling, offer draft, onboarding checklist|ATS integration and employee lifecycle|Human reviews shortlists and makes hiring decisions|
|Marketing|Campaign brief, copy/assets, approved organic post, performance report|Paid ads and CRM campaigns|Approve public content, audience and spend|
|Finance|Budget ledger, reservations, expense/invoice records, forecast|Accounting provider, reconciled payments|Authorize payments and compliance filings|
|Operations|Projects, dependencies, calendar, inventory/vendor requests, deadlines|Procurement and support integrations|Approve purchases and binding commitments|

## Acceptance goals
One complete auditable workflow per department; all external actions have a valid approval or explicit scoped policy; zero tenant leakage in security fixtures; repeated events cannot duplicate side effects; CEO status links to evidence; disconnected integrations produce blocked tasks rather than fabricated success. These are targets to test, not achieved results.
