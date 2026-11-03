# Change impact log
## 2026-11-03 — planning baseline
Status: documentation proposal only. Runtime code, dependencies, databases, credentials and deployment unchanged by this planning task.
Proposed changes: Next.js migration, Supabase Auth, durable task execution, Redis, Socket.IO, Resend, MCP, department workflows, RAG improvements, observability and staged scaling.
Main impacts: user identity mapping and session transition; frontend routes and API compatibility; approval schema versioning; durable transaction requirements; integration account setup; candidate-data protection; recurring infrastructure/provider costs.
Validation: planning consistency review and referenced official docs; no implementation tests or live integrations executed.
Rollback: retain existing application until each replacement slice passes compatibility tests; back up databases before migrations; keep feature flags and reversible deployment images.

## Required template for every future change
Date / task ID / commit or PR / author / reason / files and services / user-visible behaviour / API and schema changes / migration and backfill / auth and privacy implications / cost and performance / tests actually run and results / unverified assumptions / rollout / rollback / linked documents / remaining risks.
Append real changes only. Never mark planned work as implemented.

## Repository documentation integration
Added the planning pack under docs/, root AGENTS.md and root tasks/. Existing documents retained without deletion. Corrected cross-document paths and recorded old/new documentation roles. Verification: no destination conflicts; only Markdown additions; original tree entries preserved. No runtime tests needed for documentation-only additions. No implementation, deployment or provider actions performed.

## 2026-11-03 — Remove superseded documents
Owner explicitly approved deleting root TODO.md, COMPLETE_PROJECT_BLUEPRINT.md and FRONTEND_DESIGN_SYSTEM.md. Removed those three files, updated TECH_STACK.md's design reference and recorded the decision in DOCUMENT_REVIEW.md. Git history preserves prior contents. No runtime code or dependencies changed. Validation: reviewed Markdown references and verified the resulting Git tree; application tests not run for this documentation-only cleanup. Rollback: revert this cleanup commit.
