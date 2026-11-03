# Manual setup and validation checklist
Never paste secrets into chats, documents or source control. Use local environment files excluded from Git and deployment secret management.

1. Confirm FYP submission date, team capacity, first email/calendar provider, live-demo limits and monthly spend ceiling. Default plan: one business, Google calendar/mail integration where needed, one organic social account, all financial execution simulated.
2. Create Supabase project; configure site/redirect URLs for local/staging/production, email verification/reset and optional OAuth provider. Decide existing-user account linking/reset strategy. Verify login, logout, refresh, expired session and cross-workspace denial. Keep service-role secrets server-only.
3. Configure persistent MongoDB replica set or managed cluster and separate staging database; create least-privilege user, backup and restore test. Development in-memory mode is clearly labelled and unsuitable for durable workflows.
4. Provision Redis privately; configure credentials/TLS, persistence and no-eviction broker policy. Separate cache workload before production. Verify worker restart and broker outage recovery.
5. Create Resend account, verify sending domain with required DNS records, configure inbound domain if needed, delivery/bounce/receipt webhooks and signing secret. Send only to controlled test inboxes first. Check provider plan limits and billing in account console.
6. Create Google Cloud or Microsoft application; configure OAuth consent and exact redirect URLs; request minimum mailbox/calendar scopes; add test users; complete provider verification if required. Test grant, refresh, revoke, read/freebusy and create/cancel on a dedicated test calendar. Resend setup alone does not grant Gmail/Outlook access.
7. Configure chosen Meta app/account permissions for Instagram. Verify eligible professional account and actual API publishing capabilities against current provider documentation. Use sandbox adapter until approved. Paid ads require separate scopes, billing and spend authorization; defer initially.
8. Set Groq key/model budget, token and concurrency limits. Download approved embedding/reranking models and record license/version. Upload a non-sensitive evaluation corpus.
9. Configure storage bucket restrictions, signed URLs, MIME/size limits and malware scanning. Define candidate consent, access and deletion schedule; consult appropriate human expertise for employment/privacy requirements.
10. Set staging hostname/TLS, webhook endpoints, firewall rules, CORS and egress. Public webhook endpoints must verify signatures; database/cache/MCP remain private.
11. Configure CI/CD secrets and environments. Run unit/integration/E2E tests, backup restore and rollback exercise before live demonstration.
12. Owner sets approval roles, budgets, operating hours, deadlines and escalation contact. Test one full HR and Marketing flow with controlled accounts. Record provider receipts as demonstration evidence.

Costs to check manually: hosting, database/backups, Redis, storage/egress, AI tokens, email, monitoring and any paid ads. No price estimates are asserted here. Choose free/development tiers only after checking current limits; add alerts and hard app budgets.
