# Jobs, deadlines, MCP and knowledge plan

Updated 17 November 2026; submission target 30 November. Implement and verify in this order:

1. Mongo durable queue: deterministic idempotency keys, atomic leases, three attempts, bounded execution, restart recovery, task-outbox repair. Redis wake-up hints are optional; Mongo is authoritative. One API process owns the existing in-memory agent registry. Queue CEO drafts, saved-task briefs, document indexing and approved internal simulation actions.
2. Version-bound UTC task deadlines: reasoned edits while pending, deduplicated in-app reminder/overdue/CEO-owner escalation; no external email/calendar delivery. Block overdue execution in the common synchronous/queued execution path.
3. Official Python SDK private stateless MCP: revocable 15-minute business/department bearer capabilities, current ownership checks and request budgets. Read budget/tasks/knowledge or propose internal work. Never expose approval, publishing, credentials or arbitrary URL tools. Private bearer access is not a public OAuth server.
4. Advanced document retrieval: Markdown/text, heading/overlap chunks, source/version/department metadata, BM25+dense fusion, optional cached cross-encoder reranking, strict evidence prompts, exact quote checks and abstention. Clearly label lexical/extractive fallbacks. Reindex/update/delete must invalidate old versions. Preserve historical Chroma decision memory separately.
5. Next.js controls, README/manual steps and actual automated evidence. Test claims/retries, isolation, stale versions, MCP wire calls/revocation, actual Mongo reconnect, browser acceptance and 50 synthetic retrieval cases. No live external effects or invented success.

## Scope and manual dependencies
Install dependencies, connect durable Mongo and opt into BACKGROUND_JOBS_ENABLED. Redis is optional. Explicitly warm model caches for hybrid/reranker mode. Do not overwrite existing .env files. Production secrets, domain/HTTPS and provider connections are operator tasks; no automatic deployment.

Bounded corpus first: up to 100 documents/128 chunks per document/2,048 retrieval chunks. Normalized vectors in Mongo are not a production indexed vector service. PDF/OCR, distributed simulation workers, Kubernetes, full OAuth and external calendar/email delivery are deferred. Document evidence can inform CEO draft planning; it never grants approval or overrides the ledger. Exact quote checks do not establish full semantic entailment.

## Remaining calendar
17–20 November: complete/test these automation controls and five-department approval paths.
21–23 November: manual dataset/RAG evaluation with the user's own business examples; fix defects.
24–27 November: staging, production configuration, backups, monitoring and deployment acceptance.
28–29 November: regression, demo rehearsal and final documentation.
30 November: submission with deployed evidence. These future checkpoints are targets, not completed work.

## Rollback
Disable BACKGROUND_JOBS_ENABLED, revoke MCP grants and restore the previous application image. Retain additive collections; no destructive migration. Record actual checks in docs/impact.md and README before claiming completion.
