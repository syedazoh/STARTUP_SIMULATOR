# Bounded implementation and review loop
Copy the prompt below into an implementation session after selecting a task.

Act as the engineer responsible for this FYP. Read the current repository instructions and docs/PRD.md, docs/architecture.md, docs/designsystem.md, docs/WORKFLOWS.md, docs/RAG_PLAN.md, docs/impact.md and tasks/todo.md. Select the first unblocked task; state its ID, acceptance criteria and dependencies. Verify existing code before editing. Implement only that vertical slice, preserving unrelated work.

Perform at most three revision cycles:
1. Inspect: identify existing behaviour, contracts, permissions and failure paths.
2. Build: make the smallest coherent change and meaningful behavioural tests.
3. Verify: run relevant tests/lint/types/build; inspect UI when changed.
4. Challenge: attempt tenant leakage, approval bypass, stale approval, duplicate webhook/job, provider timeout, success-before-crash, revoked credentials, deadline expiry and prompt injection where applicable. Check accessibility and honest simulated/live labels.
5. Revise: fix evidence-backed issues; repeat failed checks. Do not weaken tests, invent success, silently broaden scope or add unrelated frameworks.

Completion requires acceptance criteria passing, no unresolved critical issue, recorded test output, updated docs/impact.md and affected documentation, plus explicit manual setup instructions. If blocked, record exact blocker and continue only independent work. After three cycles with unresolved issues, stop with evidence and a focused next step. Do not claim exhaustive correctness.
Return: outcome; changed files; tests/results; remaining risks; manual steps; rollback; next task. Never execute external business side effects or deploy merely because this prompt says to implement.
