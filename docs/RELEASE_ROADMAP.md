# Integration and AWS release plan — 18 November 2026

This is a source-backed work plan, not a deployment or live-provider readiness claim. The walkthrough is a separate, synthetic UI recording. No email, social post, permission grant, AWS resource or external spending was performed.

## What is present

- Business ownership checks, owner approval fingerprints, task review and execution statuses, credential encryption/revocation, decision history and durable collaboration projections exist.
- Dataset-driven simulation, jobs/deadlines, MCP/read-propose boundaries and retrieval features have documented tests and limits. See the existing impact log and live-integration review.
- Docker images, an ECR/EC2 deployment runbook, a private container network and Caddy TLS ingress already exist. The production Compose frontend is Vite/nginx. It does **not** yet run the Next.js executive workspace.
- The onboarding walkthrough and transcript explain business setup, CEO planning, owner approvals, handoffs and outcomes. Playback is visitor-controlled with no eager MP4 download.

## Confirmed provider choices

The owner selected **Gmail inbox connection** and **Instagram + Facebook** on 18 November 2026. Build Google OAuth connection/token lifecycle first, then Meta account discovery/consent. Reading Gmail and sending Gmail are separate capabilities: request only the scopes required for the approved feature, explain access, and complete provider verification/review when applicable. Google Cloud OAuth client configuration, authorized callback domain and controlled test identities are still required. For Meta, verify the chosen eligible Instagram/Facebook account types, app permissions and review requirements; do not treat a pasted token as complete consent/account verification. Provider credentials and grants are not configured by the walkthrough task.

## Remaining work, in order

| Workstream | Concrete next deliverable | Acceptance before live use |
| --- | --- | --- |
| Email account connection | Confirmed Gmail inbox OAuth. Add connection UI, state/PKCE as appropriate, least-privilege scopes, encrypted refresh tokens, refresh/revoke and error recovery. | Owner connects a controlled test account; cross-business reads fail; disconnect removes usable access. Supabase sign-in emails are a separate feature. |
| Approved email actions | Add bounded send/draft task contracts, adapter, preview, explicit simulation/live modes, idempotency and delivery receipt/webhook verification. | One explicitly approved message to a controlled recipient, with provider receipt and retry reconciliation; simulated output never counts as delivered. |
| Social connection | Confirmed Instagram and Facebook. Existing Instagram manual-token vault is partial; implement eligible account discovery, OAuth scopes/consent, token lifecycle and connection status. Other platforms need their own adapters. | Controlled owner account can connect/revoke; denied/expired scopes fail clearly; account eligibility is checked rather than inferred from a token. |
| Social publication | Complete hosted media/container/status processing, separate image/reel contracts, real publication-ID receipts, error/retry reconciliation and scheduling authority. | Owner-approved controlled post verified at the provider. Current caption-only/mock-token paths do not prove publication. |
| Permissions | Preserve existing ownership and immutable approvals; add provider-specific grants and app-review requirements, lifecycle/audit evidence and least-privilege roles. | Cross-tenant, stale approval, denied/revoked provider scope, webhook signature and duplicate-effect checks pass. |
| Frontend release choice | Choose the classic Vite stack or finish Next production packaging/migration and auth/environment wiring. The video explicitly identifies the executive UI. | Tested production image, matching tutorial/interface, authentication callbacks and all required routes work on the deployment domain. |
| AWS staging | Build immutable tagged images, push to ECR, stage on EC2 with Docker Compose/Caddy and private Mongo/Chroma/worker connectivity. Configure domain, secrets, backups, persistence and observability. | HTTPS, health/readiness, restart recovery, smoke tests, secret isolation and rollback verified on staging. No cloud changes until deployment is explicitly requested. |
| Latency/reliability | Measure first; then target hot paths, cold model startup, payload sizes, polling and assets. | Record baseline and post-change p50/p95, error rate, concurrency and memory under representative load. Targets below are proposed, not achieved measurements. |

## Low-latency deployment approach

Start with the existing single-region, same-origin topology: Caddy → frontend/API, with backend, Mongo and retrieval storage close together on a private network. Choose an AWS region near the actual users **and** account for managed Supabase/database locations and the model-provider path; distance between those services can dominate latency. Do not promise a region or hardware minimum without measurement.

Use a measured CPU/RAM budget for Mongo, Chroma, embedding models and application workers; the ML stack can exhaust a small instance. A t3.small in the older runbook is not a benchmarked sizing guarantee. Validate container architecture/native dependencies and peak memory before committing to instance size or autoscaling.

Keep video out of initial account-page requests: `preload=none`, a small poster, byte-range serving and a short public cache only for public `/media/` assets. For larger usage, put versioned public media/static files behind S3/CloudFront; never apply those public cache rules to authenticated business data. Avoid compressing already compressed MP4. Preserve same-origin HTTPS and connection reuse.

Measure cold/warm model calls separately from local API reads. Warm local embedding resources when appropriate, keep bounded retrieval and indexed business-scoped queries, and show progress for long generation/execution. A job queue or progress channel improves responsiveness; it does not make model inference instantaneous. Existing five-second boardroom polling means visible handoff delay can include polling plus queued visual playback; that is different from API response time.

Proposed staging budgets to agree and test: p95 warm local read APIs under 500ms at expected load, usable cached shell within 2.5s on a representative phone/network, and immediate UI acknowledgement for long-running actions. Model/provider operations need separately observed budgets and timeouts. These values are acceptance targets, **not** measured current performance or guarantees of “minimum latency.”

## Release gates

Confirm provider choices/scopes, frontend to ship, AWS account/region, domain and controlled test identities. Complete external-adapter acceptance, build/security checks, backups/restore, health/metrics, load tests and rollback rehearsal. Then deploy staging, verify there, and request the authorized production rollout. See [deployment.md](deployment.md) and [LIVE_INTEGRATION_REVIEW.md](LIVE_INTEGRATION_REVIEW.md) for current implementation boundaries; their older evidence is not new live acceptance.
