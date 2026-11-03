# Detailed business workflows

## HR: hiring a designer
1. Owner sets role, salary range, headcount, deadline and interview panel.
2. HR retrieves approved role requirements and creates a requisition. Finance checks available budget and reserves a hiring allocation. CEO reviews business need; owner authorizes opening the role.
3. HR drafts job description. Owner approves exact text and publishing destination. FYP uses an application form; external job-board publishing is a later connector, not assumed API access.
4. Applicants submit CVs with consent. Scan attachments, extract text, restrict candidate access and record retention/deletion date. Emails enter through an explicitly connected mailbox or inbound domain, not arbitrary mailbox access.
5. HR extracts job-relevant qualifications with source evidence. Missing data remains unknown. Do not infer protected traits or automatically reject candidates. Human approves shortlist and candidate communications.
6. Calendar connector reads free/busy only within granted calendars. Offer candidate slots, collect choice, recheck conflicts and timezone, then create one event with attendees and meeting link. Handle decline, reschedule, cancellation and stale slots.
7. Send interview message through Resend or the selected mailbox. Store message ID and calendar event ID. Delivery, bounce and candidate response are distinct events. A sent invitation does not prove attendance.
8. Panel records interview notes. HR prepares comparison and recommendation; human makes selection. Finance rechecks approved compensation. Offer requires authorized human approval and signature process.
9. Track acceptance/decline explicitly. “Hired” requires documented acceptance and human confirmation. Operations gets onboarding tasks, Finance gets payroll setup draft, CEO gets evidence-linked update.
10. Failed send retries safely; no response triggers reminder task; missed deadline escalates; rejected offer returns to shortlist stage. No real payroll or contract execution in FYP.

## Marketing: organic campaign
Owner brief → Marketing research with sources → strategy/copy/asset draft → brand and claims checks → Finance budget check if needed → CEO review → owner approves exact account, asset, caption and time → queue → provider upload/publish → retrieve provider status → store public post ID/URL → fetch permitted metrics → CEO report.
Start with one provider: Instagram professional-account integration if permissions are available. Maintain a clearly labelled sandbox adapter otherwise. Asset generation is separate from publishing. Asset rights and human review are recorded. Deleting a published post is a new authorized action.
Paid ads are a later vertical slice using Meta Marketing API or Google Ads API, each requiring its own account, scopes, billing and approval. Require total/daily caps, audience, dates, currency and stop conditions; retrieve actual spend and pause on threshold. Posting organically never means an ad was purchased.

## Finance
Expense/invoice request → validate vendor/document → duplicate check → category and budget availability → approval → reserve funds → create accounting record or simulated payment → receive/retrieve outcome → reconcile ledger → release unused reservation → CEO update. Store money as integer minor units and currency. Pending transactions are not paid. Uncertain provider outcomes require reconciliation before retry. Real bank credentials/payments excluded initially.

## Operations
Objective → project/milestones → dependency graph → assignments → deadlines/calendar → reminders → evidence review → completion. Block dependent work when prerequisite is missing. Procurement follows quote → budget approval → owner authorization → order → receipt confirmation. Inventory decrements require validated events; customer support triage can create tasks, but promises/refunds need scoped authority.

## CEO and owner reporting
Every department emits structured durable events: task.proposed, approval.requested, task.blocked, task.executed, task.verified, task.overdue and budget.changed. CEO dashboard reads a projection of task and ledger facts. Summary job combines these facts with scoped retrieval, cites task IDs and marks missing evidence. Show daily summary, immediate critical blockers, spend versus allocation and approaching deadlines. A summary failure must not stop task execution. Owner can inspect every child task and override a plan with an audit reason.

## Email and calendar boundaries
Resend supports application outbound and configured inbound email; it does not automatically read an existing Gmail/Outlook inbox. Use Gmail API or Microsoft Graph with OAuth for existing mailbox reading; choose one first. Google Calendar API or Microsoft Graph manages calendars. Consent, scopes, token refresh, revocation and provider verification are manual setup dependencies.

## Completion evidence
Email: provider message ID plus delivery state; meeting: event ID plus attendee response; hiring: human decision plus accepted offer evidence; post: published provider ID/URL; ad: campaign ID/status and actual spend; purchase: order and receipt; task: expected deliverable reviewed. UI must display pending/unverified states honestly.
