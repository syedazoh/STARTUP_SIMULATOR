# Documentation review — 3 November 2026

No existing document was deleted or changed. Recommendations below require owner decision before removal or archival.

|Existing file|Finding|Recommendation|
|../TODO.md|Completed one-off vulnerability/import repair checklist; zero-vulnerability wording and historical versions should not serve as a current security verdict.|Candidate for archive or deletion after owner approval; retain relevant historical evidence.|
|../COMPLETE_PROJECT_BLUEPRINT.md|Calls itself the standalone execution spec but mixes old plans and implemented behaviour; includes Next.js/WS and older RAG/model descriptions.|Archive after approval, or mark historical and link the new PRD/architecture.|
|../FRONTEND_DESIGN_SYSTEM.md|Charcoal/cyan cyber-minimalism conflicts with proposed Emerald/Champagne/Lavender direction.|Archive after owner confirms replacement; new designsystem.md is a proposed direction, not a completed token specification.|
|../TECH_STACK.md|Useful inventory, but includes ambiguous embeddings/test runner descriptions and realtime claims that need implementation verification.|Keep and revise in a separate documentation update; do not delete.|
|../TASKS.md|Historical implementation decisions and validation evidence.|Keep. New tasks/todo.md is prospective work, not its replacement.|
|IMPLEMENTATION_CHECKLIST.md|Unfinished reliability/security findings and detailed evidence.|Keep and reconcile during T01; do not discard unchecked work.|
|CEO_SUPERVISION_AND_SESSIONS.md|Useful session/task explanation; some remaining-work entries overlap newer ledger milestone.|Keep; cross-reference newer ledger documentation in a later cleanup.|
|CEO_TASKS_AND_LEDGER.md|Concrete implemented ledger and supervision semantics and limitations.|Keep.|
|AI_TROUBLESHOOTING.md|Operational diagnostics and configuration guidance.|Keep; provider facts require periodic verification.|
|DOCKER_LOCAL_SETUP.md|Practical local setup and wiring checks.|Keep.|
|deployment.md|Existing deployment runbook, separate from future architecture.|Keep; update when deployment changes.|
|BRANCH_CONSOLIDATION.md|Dated repository-history and validation evidence.|Keep as history.|
|../README.md|Application entry point.|Keep.|

New-plan reading order: PRD.md → WORKFLOWS.md → architecture.md → ../tasks/plan.md → ../tasks/todo.md. Links/paths inside the planning prose are repository-root-relative unless Markdown links specify otherwise. New documents describe proposed expansion; inspect runtime code and current operational guides for present behaviour.
