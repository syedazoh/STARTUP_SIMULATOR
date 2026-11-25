# 25 November 2026 delivery

## Start here

Open **http://localhost:3000/login** after starting your original MongoDB, FastAPI on 8000 and Next (`cd web`, `npm ci`, `npm run dev`). Keep your existing Supabase project and original Mongo URL **and database name**. Exact Windows commands and configuration: [local recovery](LOCAL_ACCOUNT_RECOVERY.md). Exact code-email settings: [sign-in guide](AUTH_ENTRY_2026_11_25.md).

Retained agents: CEO, Finance, Marketing, Operations and **HR**, as confirmed by the owner. Strategy does not replace HR in this release.

## Login root cause and fix

The documented `web` command serves Next on 3000, while `frontend` serves classic Vite on 5173. They previously had independent Supabase/native sessions. Return paths were lost, and an unlinked verified identity correctly could not access an original native account. A separate classic API-client bug omitted the bearer header on protected `/api/auth/me` because it excluded every `/api/auth/*` endpoint.

Next now retains the familiar page with an existing-user email-code request, same-screen verification, resend/error recovery, pending-email reload and protected return. Registration remains separate; password sign-in remains an explicit fallback. Successful default sign-in opens a single existing business or the selector. Classic login redirects to Next; retained classic pages restore a revocable native session from the verified Supabase cookie through an Origin-checked same-host bridge. Tokens are not placed in URLs/localStorage. Both logout paths revoke/clear sessions; appearance remains. Unlinked identities still require the original native password and verified matching email in the existing ownership-link form. Email alone never transfers ownership.

**Supabase setting:** in the existing project's Authentication → Email Templates → Magic Link, include `{{ .Token }}`. Enable Email sign-in, use localhost:3000 as the local Site URL and allow configured callback/confirm URLs. Keep normal confirmation enabled. Check SMTP/delivery and rate limits if no email arrives. Both apps/backend must use the same existing project; use localhost consistently across ports.

Initial safe inspection found no usable provider configuration or backend listener in this checkout. The fixes establish source/runtime behavior with a disposable fixture; they do not establish why the owner's private Windows account failed or prove recovery of their original business. Never send secrets, passwords or email codes in chat.

## Implemented behavior

- Common business-scope instructions preserve agent roles. Record-backed queries/definitions/clarifications avoid unnecessary model calls; other conversation requests receive recent conversation plus bounded authorized business/task/ledger context. Answers carry source labels. Unclear terms ask one question, missing calculations request evidence, unrelated requests receive one scope redirect.
- All five workspaces can save a recommendation with what/why/decision and user-started English speech of exactly that explanation. Stop and unavailable-voice text fallback remain usable. Templates, owner drafts and structured Finance evidence are labelled; they are not claimed to be autonomous LLM decisions.
- One saved record is reused in workspace/boardroom through **existing CEO plans**. Marketing compares two captions, audience and rationale; Finance compares proposed promotion with current simulated funds. Owner-recorded CEO review supports revision feedback, rejection and approval. A deterministic assignment ID plus existing task pipeline ensures one Marketing task under repeated approval, concurrency and lost-response retry. Final task execution still requires the existing owner approval. It saves an internal draft, publishes nothing and spends zero. Other role recommendations are advisory; their existing proposal forms remain the action entry.
- Emerald/Champagne/Lavender palettes work independently of surface presets and light/dark/system. Same-host appearance preferences survive navigation, reload and logout. Chart/tooltip/focus/form colors use shared tokens.
- Status donut and workload bars reconcile to the selected business's displayed latest-200 task table. Unknown states/roles remain counted. Empty/error states are explicit. Trends require actual timestamps and finite values; a line needs two observations. No invented ticks or currency.

## Actual response samples

These are real API/service outputs from disposable test records, **not live Groq**. Full machine-readable outputs, including the saved task ID, are in [evaluation/nov25](evaluation/nov25/conversation-responses.json).

| Input | Actual response | Evidence |
| --- | --- | --- |
| Which Marketing tasks are waiting for approval? | “Marketing has 1 task(s) waiting for owner approval in Acme Inc.” followed by the saved task ID and “campaign launch” | Deterministic authorized task query; [full output](evaluation/nov25/clear-task-response.json) |
| What is a T? | “Where did you see ‘T’ in the simulator?” (typographic quotation marks in JSON) | Deterministic clarification; no task/model call |
| It is the total in the task-status donut chart. | “The center total in the task-status donut is the number of loaded tasks for Acme Inc: 0. Each task contributes once to a status segment. The chart is limited to the latest 200 tasks, not a lifetime total.” | Deterministic definition with test-business count |
| What does runway mean? | “Runway is how long a startup can keep operating before its cash runs out. A simple estimate is available cash divided by monthly net cash burn; no account data is needed to define the term.” | Relevant general definition |
| Can we afford this campaign? | “I do not have a recorded available balance for this business. Check Finance’s simulated ledger and tell me which campaign budget you want reviewed.” | Missing-data fixture, no invented budget |
| Give me a pancake recipe | “I can help with your startup and this simulator. Would you like to review your team’s pending tasks?” | Scope redirect |
| How should we prioritize our current business workload? | “For this recorded workload, review the pending Marketing proposal first.” | **FakeChatLLM test double**, not live inference; [output](evaluation/nov25/model-double-response.json) |

The separate browser fixture had three existing tasks and returned the actual loaded count, one pending Marketing task, missing monthly burn for a startup runway calculation, and no other tenant's records. That fixture differs deliberately from the zero-task unit example above.

## Validation and limits

- Backend focused auth/identity/chat/tasks/isolation/supervision/ledger acceptance: **116 passed**. Final recommendation/grounding regression suite: **6 passed**, including unsupported social-publication claims, concurrent approval and interrupted assignment recovery. Provider/model/DB were doubles in these focused tests. One upstream MCP/Pydantic warning remains.
- Next: **39 unit tests**, TypeScript and production build passed. Classic: **68 unit tests**, ESLint and production build passed. Existing classic large-bundle warning remains; latency is not measured or claimed fixed.
- Real Chromium against production Next, actual FastAPI routes/services, **mongomock plus a local identity-provider double**: existing-user code flow; incorrect/expired codes; resend; pending-screen reload; SDK refresh; protected return; selected existing fixture business; direct grounded questions; exact narrated text/Stop; saved revision/feedback; double approval → one draft task; reload; four-task chart reconciliation; six palette/mode combinations at desktop/390px; classic verified restoration and identity lookup; logout; no bearer in localStorage; HttpOnly/root refresh cookie. **No page errors.** [Result](evaluation/nov25/browser-result.json).
- Additional browser confirmation covers no-voice text fallback, main logout/protected redirect and compact desktop/mobile chart legend. Review caught and corrected React 19 SVG-title hydration and inherited oversized legend rows; no warning suppression or weakened assertions. Review was inline, not independent.
- `npm audit` reported **zero vulnerabilities** for both current frontend lockfiles. GitHub’s push response separately reported **22 repository alerts (3 critical, 10 high, 9 moderate)**; these existing cross-repository/dependency alerts were not resolved or reclassified in this change, so the npm result is not a clean bill for the whole project. Compose schema validation passed. Clean local Next Docker packaging passed (image `bd9366d14e6a`), including all shared modules, 39 tests, production build and type checking. No container was deployed.

**Not verified:** live Supabase email/SMTP, the owner's private Mongo records/link, live Groq answers/voice audio quality, separately hosted cross-domain classic SSO, Jenkins/AWS rollout or production latency. Browser speech was intercepted to verify exact text/English and Stop; actual voice availability depends on the device. No real social communication, credentials, payment, database migration, deployment or environment publication was performed.

## Walkthrough for today

1. Sign in at localhost:3000 with the existing Supabase email and latest emailed code. If original businesses are missing, verify original Mongo URL/database and use the one-time ownership-link form; do not create replacements.
2. Open your business → **Marketing workspace**. Enter two captions, select one, audience/rationale and proposed promotion amount (zero is fine). Save the recommendation.
3. Read what/why/decision; use **Hear recommendation**, then **Stop**. Text always remains available.
4. Open its boardroom link. Review Finance evidence and the saved proposal. Request revision with feedback if needed; return to Marketing, edit and save a fresh revision.
5. In boardroom, **Authorize CEO plan & assign**. Refresh: the same decision and one Marketing draft task remain. This records owner authority, not an autonomous CEO verdict.
6. Open Marketing tasks and inspect the assigned payload. The existing owner task approval saves the simulation draft artifact; it never publishes or starts promotion. The backend regression verified zero financial change.
7. Open Overview and expand the task table: donut/workload counts match. Appearance remains available everywhere; choose a palette/mode and refresh or sign out to check persistence.

## Repeat isolated acceptance

Use the existing backend dependency image only on disposable local storage. `scripts/studio-browser/nov25_backend.py` refuses startup without `SIMULATOR_FIXTURE_ONLY=1`; it supplies fake identity and Mongo only, and must never be deployed. It uses port 8013. Run Next with fixture provider/backend settings on localhost:3025, classic on localhost:5175 with proxy targets 3025/8013, then `node web/tests/nov25-journey.browser.cjs`. Restart the fixture before each run to reset its seeded tasks. The fake verification code is confined to fixture/test source and is not a real credential. The production image does not copy the fixture.
