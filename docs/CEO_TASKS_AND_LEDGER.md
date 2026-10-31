# CEO assignments and shared financial ledger

This milestone adds mandatory recorded CEO authorization, department task dashboards,
a shared financial ledger, and background report review. It does not deploy the app.

## Task flow

Every manual, chat, API event, simulation and CEO plan action uses the shared task
service. Both the department and CEO must be enabled. A validated routine numeric
proposal receives a recorded CEO operating-policy decision. The policy escalates
funding shortfalls to owner review; execution still checks current funds. An
owner-activated CEO plan authorizes its matching assignments. External publication
requires a successful structured AI review; unavailable AI leaves it pending.

CEO authorization precedes owner approval or configured department auto-approval.
An authorization is not execution, a promise of available funds, or proof that a
business objective was achieved. Every execution requires `ceo_authorized=true` and
an atomic approval claim. Existing unreviewed tasks receive CEO review before owner
approval. Revising a task invalidates its previous authorization and checks again.
Concurrent reviews are claimed atomically. Interrupted authorization can be retried
after its 60-second lease expires, using the Retry CEO review button.

Open a department's page to see its latest 200 tasks, including CEO assignments,
objectives, success criteria, decisions, statuses and results. Completed/failed work
remains visible. The CEO page shows all departments; the CEO-only checkbox filters
plan assignments. Owner review actions do not impersonate an autonomous department
worker. Manual-mode assignments wait for owner approval. Auto-mode assignments run
only within the configured limits.

Execution evidence is persisted as a department report before narrative review.
Up to four reviews per business run outside its execution lock, with a 20-second
model timeout. Routine successful work without explicit success criteria gets a
policy acknowledgment. Other outcomes receive AI review or an owner-attention
fallback. Pending/expired report leases resume when reports or new work are
accessed. This is bounded in-process background work, not a separate durable worker
service. It does not automatically create new plans or retry consequential actions.

## Financial semantics

`GET /api/businesses/{id}/finances` and the Finance page expose:

| Balance | Meaning |
| --- | --- |
| Cash | Money still held by the simulated business |
| Reserved | Outstanding execution holds and unused departmental allocations |
| Available | Cash minus reserved funds; also Finance's budget-pool metric |
| Expenses | Actual settled task costs, not allocated budgets |
| Monthly payroll commitment | Salary obligation for hires made through this ledger |

Money is rounded to integer cents. One Mongo document atomically stores balances,
reservations and journal entries using version comparisons. A task reserves its
maximum cost before mutating agents. Allocations for its department (or General)
fund actual work first, with any remainder using free cash. Failure or denial
releases the hold; partial work restores unused allocation funding. Repeat
settlement and revenue events are idempotent. Releasing an allocation is blocked
while it funds an executing task. Release unused budget from its Finance task card.

- Finance budget requests allocate funds; they do not spend cash.
- Marketing campaigns settle the actual Finance deduction.
- Recruitment charges the first month's salary for approved hires and records the
  monthly commitment. Default salary is $3,000 per hire; forms allow an explicit cost.
- Operations charges approved quantity times unit cost, default $100 per unit.
- Existing simulated income remains $8,000 every five ticks; it now posts once to
  the ledger per run/tick. It is still demo income, not causal sales revenue.

An interrupted financial settlement leaves a `reconciliation_required` task and
retains its hold. Do not retry its side effect; inspect the journal and execution
evidence. Reconciliation is not yet automated. Financial journal capacity is bounded
at 5,000 entries per business; archival/migration is needed before that limit.

## Persistence and current limits

Existing businesses open the ledger from their current restored Finance state.
Past allocations/costs cannot be reconstructed and are not invented. Newly created
accounts persist in MongoDB. Development in-memory fallback still loses all records
on restart. The ledger protects financial writes with optimistic concurrency, but
agent objects and simulation state still require a single backend process; this
is not a distributed execution engine. Existing headcount is not backfilled with
invented salary commitments. Recurring payroll is not yet scheduled.

Next milestones: causal revenue and recurring operating costs, continuous CEO
replanning from measured outcomes, outcome-aware RAG, and recovery/evaluation.

## Manual acceptance checks

1. Start MongoDB, backend and frontend; sign in and open a business with CEO and
   departments enabled. Configure a working Groq key for CEO plan generation.
2. Ask the CEO to plan a small goal, activate the draft, then open each assigned
   department. Verify its objective, target and task appear only in that department.
3. Approve a manual-mode assignment. Verify the result stays on its department page
   and a matching report appears on the CEO page.
4. Allocate $1,000 to Operations. Cash and expenses should stay unchanged; reserved
   rises $1,000 and available drops $1,000.
5. Approve an Operations task for two units at $100. Cash and expenses change by
   $200, reserved drops $200, and the remaining allocation is $800. Release it and
   verify the remaining $800 becomes available.
6. Revise a pending task's cost. Verify a new CEO decision is recorded. Attempt a
   request above available funds; verify it cannot overdraw the ledger.
7. Remove/disable the AI key in a development test. External publication proposals
   should remain pending CEO review and cannot be approved for execution. Restore
   the key and retry review.
8. Restart the backend with Mongo running. Verify financial balances and completed
   assignments survive. Another account must not access them.
