# Agent workspace recovery — 24 November 2026

## Cause and result
The Next migration lacked dedicated role pages; the original Vite agent pages were still present. Added five Next business-scoped routes using existing authorized backend services, original proposal/approval controls and shared metric configuration. Added company/boardroom/navigation entry points. Four departments expose mode and policy controls, while CEO exposes planning. Chat saves the existing conversation and reports provider failures; navigation performs no writes. An in-flight guard prevents rapid duplicate messages.

Company selection now explains the identity/data split and original-password linking. Error messages distinguish rejected credentials, backend failure, conflicting identity and Supabase verification. No real account, ownership or Mongo record was migrated by this change.

## Visual behavior
Shared real procedural Three.js avatars identify each role on both frontends. Fixed backgrounds extend through landing and workspace footers. Motion controls persist, and reduced-motion/WebGL fallbacks remain available. Desktop sidebars scroll to all agents. Pending-task buttons wrap at 320px. Captures are local test artifacts under /tmp/agent-workspaces, /tmp/dashboard-reference and /tmp/agent-landing-regression. Review was inline, not independent.

## Verification and limits
Next 31 unit tests and production build/typecheck passed. Vite lint, 63 unit tests and production build passed. Browser checks use disposable localhost identity/API or intercepted synthetic responses: all five pages, role avatars, acknowledged mode save, saved chat and AI failure, account-link errors/success, sidebar scrolling, unknown-role 404 and responsive layouts. Separate checks cover classic pages, both landing themes and video playback, and background pause/persistence/reduced-motion/footer. Clean Next Docker packaging includes the shared metric config; no image was published or deployed.

These checks do not verify the owner's private Supabase/Mongo connection, real email/social credentials, AWS latency or live provider execution. Marketing publishing/media/connected-account UI still lives in classic Vite; this is explicitly linked and documented. Existing Vite bundle-size warnings remain. See ../LOCAL_ACCOUNT_RECOVERY.md for local recovery steps.
