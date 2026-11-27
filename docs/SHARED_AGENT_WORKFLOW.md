# Shared five-agent launch workflow

CEO, Finance, Marketing, Operations and Strategy share one conversation service, role configuration, artifact format and image job flow. HR remains a legacy route; existing HR records are retained. Native email/password login is active; Supabase is disabled by default. This change neither migrates accounts nor replaces an existing business.

## Run locally

Use the existing original MongoDB connection and signing/encryption keys in private `backend/.env`. Do not create a replacement database to recover a missing business. From the repository root, activate the Python environment and run:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```bash
cd web
npm ci
npm run dev
```

Open http://localhost:3000. `web/.env.local` needs `BACKEND_URL=http://127.0.0.1:8000`; no public provider key is required. Use the original native account password. A 401 refresh means the saved session is invalid/expired: sign in again. A refused connection means FastAPI is not running at the configured port. A successful empty company list is different from a failed lookup; check the original account and database before creating anything.

Optional server-only configuration:

| Setting | Purpose |
| --- | --- |
| `GROQ_API_KEY`, `GROQ_MODEL` | Current model, through the existing shared LLM client. No key produces an explicitly labelled structured fallback. |
| `BACKGROUND_JOBS_ENABLED=True` | Existing Mongo-backed worker for reference indexing, approved execution and image jobs. |
| `OPENAI_API_KEY`, `IMAGE_MODEL=gpt-image-1` | Shared illustration tool. Provider billing may apply when explicitly requesting images. Never put this key in `NEXT_PUBLIC_*`. |
| Existing RAG settings/cache | Reference retrieval with source IDs; structured records handle calculations. Enable downloads only deliberately. |

Missing image configuration returns a visible error; typed conversations and record calculations remain usable. Browser speech support varies and may use a browser/vendor speech service. Dictation is optional, reviewed before sending, and has no app-side audio-file retention. Typing is always available.

## Five-agent demo

1. Sign in and select **Open fictional five-agent demo** on the company selector. It creates/reopens a separate designated Sprout business; existing companies and prior demo work stay intact. Download its labelled JSON if needed. All startup amounts are simulated USD cents. Starting available funds: USD 300.
2. In CEO's workspace, ask for a launch plan. Review the recommendation, evidence/assumptions and options. Chat alone creates no assignments or approvals.
3. In **Coordinate a launch**, enter a goal and proposed deadline, save the draft, inspect its four assignments, then select **Authorize & assign four follow-ups**. The existing task/approval services create exactly one Strategy, Finance, Marketing and Operations task for that plan.
4. Open each personal workspace. Choose **Discuss this assignment**, then Send. Review and optionally edit the recommendation. Finance can answer “Can we spend $400 on this campaign?” from the saved balance: USD 100 gap. Operations uses saved capacity/deadlines; Strategy compares positioning; Marketing follows the saved brand.
5. When relevant, enter an image brief and explicitly generate a draft visual. Progress/failure appears in the shared job list; Preview/Download use authorized content routes. **Revise image** selects the saved parent. Check **Include in next submission** for images belonging to the same task. No social publishing occurs. Data charts are rendered from data, not generated as images.
6. **Submit this version to CEO** links immutable artifacts to that task and launch plan. In the existing boardroom select CEO and review each exact submission. Request changes with feedback on one department. That feedback appears in its workspace.
7. The assigned agent generates a changed recommendation, or the owner uses **Edit draft** if inference is unavailable. Submit the new version. Prior drafts/images remain available. Approve only after inspecting the new exact payload. Stale approval fingerprints fail. Approved internal briefs produce saved execution/report evidence and spend nothing.
8. Reload to inspect saved conversations, artifacts, assignments and decisions. Workspaces poll saved snapshots every five seconds while visible; existing task/event channels continue to drive boardroom handoff visuals. The animation itself grants no authority.

Use microphone → Finish dictation → review → Send. Starting dictation, typing, Stop audio or leaving the workspace cancels stale playback. Follow-up selection identifies the artifact being revised/compared inside that agent's conversation. Foreign references are rejected. A missing reference triggers clarification.

## Historical retail data

The Data laboratory (`/workspace/<business>/demo`) provides bounded CSV/JSON preview/import and exact GBP totals, product demand and cancellations. Import is scoped to the business owner, bound to the preview digest and idempotent for the same normalized batch. The latest batch is the analytical snapshot; overlapping imports are not cumulatively added. Imported rows never enter the simulated cash ledger or execute tasks.

The official UCI download is currently blocked in the development environment. **No UCI rows are bundled or claimed imported.** See [DATA_SOURCES.md](../DATA_SOURCES.md) and [the retail dictionary](../datasets/retail-uci-v1/README.md). When access is available, verify official attribution/license, obtain the workbook and run `python scripts/prepare_uci_retail.py <workbook.xlsx>`. Inspect the generated provenance and then preview/import the transformed file. Never substitute synthetic arithmetic fixtures as UCI observations.

## Evaluation and verification boundaries

`datasets/agent-conversations-v1/examples.json` contains 40 authored synthetic examples: six development and two held-out per agent. The app does not load them as facts or put held-out answers in prompts. The evaluator runs the real conversation service against an isolated mock database; it records actual outputs and task-creation invariants for human review, without passing expected answers to the model. Some scenarios need richer fixtures and are explicitly marked; no automatic model-accuracy claim is made.

```bash
# backend/test dependencies installed, from repository root
python scripts/evaluate_agent_examples.py --split development --output /tmp/development-results.json
python scripts/evaluate_agent_examples.py --split held_out --output /tmp/held-out-results.json
```

Inspect response mode and errors. Fix instructions, retrieval and data access first. Fine-tuning is deferred until repeated measured failures justify it. Local fixtures do not prove real Mongo persistence/restart, live image/model quality, real microphone permission/voice quality, original-account recovery or AWS deployment. See the delivery report for checks actually run.

## Storage and approval boundaries

- Conversation identity derives from authenticated owner, business and role; bodies cannot supply owner/business identity.
- `conversation_turns` uses request keys and leases; `agent_artifacts` retains immutable drafts and bounded validated PNGs. Stored image bytes are excluded from JSON history.
- `ceo_plans` + existing tasks carry the shared launch link; `agent_brief` is a zero-cost internal output, not a campaign/hire/payment tool.
- All assignment/submission/approval mutations use server authorization; approval fingerprints bind exact material fields. Revision revokes prior authorization.
- Image jobs reuse the existing durable queue. Confirmed rejections can retry the same job; uncertain provider outcomes require reconciliation rather than blind duplicate generation. Provider-start journaling prevents recovered workers from silently creating a second paid request.
- Three MiB per stored PNG and 1–1000 retail rows / 1 MiB per upload are intentional demo bounds. Monitor artifact growth before production use; these limits are not a high-volume storage design.

Rollback: revert this release and retain its additive collections. Do not drop real businesses/users/ledger data. Existing native auth, legacy chat and original deterministic HR launch demonstration remain separate compatible paths.
