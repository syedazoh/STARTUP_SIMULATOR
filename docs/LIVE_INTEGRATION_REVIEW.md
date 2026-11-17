# Live integration review — 17 November 2026

Reviewed main bc19bf8. This is a code/configuration and existing-CI evidence review, not a live-provider test. No email, post or ad was sent. The user's local Windows environment and connected provider credentials were not inspected.

## Current status

| Area | Evidence | Conclusion |
| --- | --- | --- |
| CI | Latest Backend Tests 44034274990, Docker Wiring 44034274877 and Next.js 44032957272 all completed successfully | Earlier failed Next runs remain in Actions history; later corrections passed. Green CI does not prove live external delivery. |
| Jobs, deadlines, MCP, document retrieval | Existing 476-test backend evidence, browser flows and 50-case synthetic retrieval evaluation | Implemented within README's documented bounds. Not proof of the whole startup operating autonomously. |
| Business email | No Resend/SMTP business send service, mail action contract or delivery webhook implementation found in application sources/dependencies | Not implemented, rather than a disabled switch. Supabase authentication emails are a separate managed auth function. |
| Instagram publishing | services/social.py, credential vault and owner-approved marketing task routes exist | Partial adapter. Manual token connect exists; a complete OAuth/account verification flow does not. No live provider acceptance evidence. |
| Reels | reel_request is routed to the same caption-only Instagram handler | No implemented video upload/media-type/status-polling flow. |
| Calendar | No business calendar/free-busy/event integration found | Not implemented; in-app deadline notifications do not create meetings or send email. |
| Automatic external execution | services/jobs.py SAFE_ACTIONS includes internal simulated actions/dataset launch; MCP exposes read/propose tools | External email/social execution is deliberately outside this worker/MCP slice. Approval routes do not imply an enabled live integration. |

## Concrete publishing gaps

- InstagramPostAction accepts only content. The current media-create request sends caption/access_token but no image_url or video_url. Meta's content-publishing flow requires media input/container handling, then publication. Reels need video input/media_type plus processing handling. Official reference: https://developers.facebook.com/documentation/instagram-platform/content-publishing (reviewed 17 November 2026).
- social.py ignores the publication response body and returns the creation/container ID as media_id. Live completion must retain the actual published media ID and verifiable outcome, separately from container IDs.
- Debug test-token branches return status posted with test_media_id without contacting Meta. Existing credential/post tests validate this simulated path; they do not prove a real Instagram post. Explicit simulation labels and tests for the real HTTP contract are required before calling this production-ready.
- Owner-connected provider tokens, eligible account/permissions and hosted media have not been verified against the user's real account. Do not infer those are configured or absent from repository contents alone.

## Required implementation sequence

1. Email: approved-task email contract, Resend adapter, clear simulation/live mode, idempotency, delivery-event signature verification and outcome records. Operator then configures sending identity/domain/key and a controlled test recipient; validate delivery before broader automation.
2. Publishing: complete media assets/validation, selected Meta login/account/scopes, container creation/status handling, published-ID receipts, provider error handling and reconciliation. Explicitly distinguish simulated output from actual posts. Verify one owner-approved controlled post before automatic scheduling.
3. Only after those adapters work: extend durable job handlers with external-effect idempotency/reconciliation, preserve CEO/owner authority and expose real delivery/publication evidence. Calendar access is a separate integration.

## Verification boundary

Existing successful CI runs were rechecked through GitHub. Source paths, action contracts, credentials, worker allowlist and simulated posting tests were inspected. A fresh focused local pytest attempt could not start because the temporary test virtual environment no longer exists; no new local pass is claimed. No runtime code was changed by this review. Follow-up implementation and real-account acceptance remain open.
