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

## 2026-11-03 — Add opt-in Supabase authentication preview
Added separate Next.js `web/` app (signup, email confirmation, login/logout, protected business list, original-account linking), server-only HttpOnly cookie handling and CI build/type/audit checks. FastAPI supports explicitly selected Supabase bearer authentication using provider validation; preserves Mongo ownership and local roles. Existing account linking requires native session plus verified same-email Supabase identity. Supabase-only users cannot log in via a missing native password hash. Added config examples and docs/SUPABASE_AUTH_SETUP.md. No existing user IDs, business ownership or encryption keys migrated/deleted. No production deployment, credentials or live email actions performed. Exact validation results are recorded below after checks. Rollback via commit revert; original frontend remains available.

Validation for authentication slice: 54 focused backend tests passed against the repository's pinned direct requirements (test_supabase_auth.py, test_auth.py, test_execution_supervision.py, test_businesses.py; mocked Mongo/provider). Next.js production build and strict TypeScript checks passed; production dependency audit reported zero vulnerabilities. Local production HTTP login-page smoke passed. git diff --check passed. No live Supabase email/login, real Atlas migration, browser interaction/accessibility audit or deployment verified. Old frontend remains unchanged. Additional production monitoring/rate limits and the full Next.js UI migration remain open work.
