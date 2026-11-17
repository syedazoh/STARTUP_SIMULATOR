# Purple 3D executive studio

## Open the Next.js version

From the complete repository checkout:

```bash
cd web
npm ci
npm run dev
```

Keep the existing FastAPI backend running. Open http://localhost:3000, sign in using the existing Supabase flow, and select **Enter executive studio** beside your business. Route: `/workspace/<businessId>/boardroom`. Existing account linking and the synthetic launch laboratory remain available. The public home, authentication and workspace pages now share the dark identity.

The existing React/Vite app remains available using `cd frontend`, `npm ci`, `npm run dev` (port 5173). Its dedicated Boardroom and surrounding application surfaces use the new palette and the same procedural 3D scene. Existing routes and approval controls are preserved.

## What is interactive

- Select a physical avatar or an accessible team button to inspect that department's loaded tasks and backend state.
- Drag the floor to orbit the camera. Reset camera restores the overview.
- Choose **Preview a task handoff** to see a bounded, synthetic delegation/review/owner-approval/delivery sequence. It makes no mutation request. Exit preview removes the packet immediately, including on reduced-motion devices.
- Choose the expand icon to enter immersive view. It has an opaque backdrop, keyboard focus containment and an Escape-key exit. The follow-handoffs control is optional; automatic camera motion is off initially and suppressed by reduced-motion preferences.
- Open **Review exact action** in the approval inbox before approving/rejecting. Approval uses existing server ownership checks and may execute that action immediately. Preview does not expose real decision buttons.
- Use **Team list** if WebGL is unavailable, the context is lost, or you prefer ordinary controls.

## Truth and motion

Next.js retrieves up to 200 tasks, 100 backend events and the agent snapshots through authenticated server functions, polling every five seconds while visible. The initial successful snapshot is a baseline: past work does not animate as fresh activity. Subsequent task-state changes and supported explicit/backend-established event routes can animate packets. Unsupported routes are omitted. A CEO plan with persisted provenance can show delegation; owner decisions originate at the separate approval desk. Arrival animation is presentation and never authorizes or completes a task.

Ordinary execution and verified completion remain distinct labels. Counts describe the loaded task window, not company-wide analytics. The inbox displays up to eight pending tasks at a time; subsequent refreshes expose the next pending work as decisions are processed. Connection failures show a recovery message and retain last available records. Missing snapshots do not imply an agent is available.

The Vite Boardroom retrieves its own authenticated, business-scoped snapshot of up to 200 tasks every 1.8 seconds while visible, leaving the actionable approval queue unchanged. Both studios observe persisted status changes without interpreting disappearance as acceptance. New assignments are queued individually (up to 32 pending visuals), so a multi-department CEO plan displays each connection in order.

Handoffs use a bright raised line, directional arrowheads, a moving document packet and a receiver highlight. A readable route card identifies sender, receiver, task and visual phase. The last route remains visible until replaced or explicitly cleared; “Task visual arrived” describes the animation, not business acceptance. The synthetic preview begins with CEO → Finance: Review department budget, then follows a twelve-step illustrative launch meeting in which all five executives both send and receive work. A selectable participant strip names each department’s current visual role and counterpart; matching avatar labels distinguish sender and receiver. “No active transfer” describes only the visual exchange, not department availability.

Both clients queue every newly observed routed event, not just the last event of a polling batch. Explicit sender/receiver records support all twenty directed pairs among the five departments. For implicit routes, recipients come only from inspected EventBus subscriptions and negotiation/arbitration wiring; external/manual/system sources and self-routes do not generate department-to-department transfers. Known numeric, Mongo ObjectID and UUID agent-instance suffixes normalize to department names. Live playback pauses while previewing or while the tab is hidden; illustrative routes never create backend work.

## Implementation

`frontend/src/studio/model.mjs` contains the shared state-to-visual mapping and collision layout. `scene.mjs` builds the avatars, workstations, approval station, geometric portals, camera and task packets directly in Three.js. These are authored robot meshes, not imported rigged characters or video. Placing the core inside `frontend/` preserves the existing frontend-only Docker context. Next.js expands its Turbopack/tracing root to the repository to share the framework-neutral core without mixing React 18 and React 19 renderers. Next adds Three.js 0.170.0 and its development types; existing Vite dependencies remain.

The scene caps device pixel ratio, pauses rendering in hidden tabs, uses static rendering for reduced motion, and disposes GPU resources/listeners on unmount. It does not require model, texture or font CDNs. Manrope is self-hosted with its OFL license in each app's `public/fonts/` directory.

## Checks

```bash
cd frontend
npm test
npm run lint
npm run build
cd ../web
npm test
npm run typecheck
npm run build
```

The shared behavioral tests are in `frontend/tests/studio.test.mjs`. Browser acceptance uses a disposable local identity/API fixture and synthetic records; it verifies actual WebGL and production Next.js behavior, not live provider readiness. No backend implementation or credentials were changed. Mobile geometry labels, preview cleanup, normal and reduced motion, avatar/list selection, approval result refresh and immersive keyboard exit are covered by the session's browser checks. Legacy Vite build retains an existing large-bundle warning.

## Reference boundaries

User supplied HelloRun as a reference for immersive 3D movement. Its pasted HTML describes a speed/rhythm runner. The live site and screenshot hosts returned environment-network 403 during this work; direct gameplay fidelity is unverified. No third-party game art, audio or source was copied. The user specified the black/purple/beige palette. Figma tools and the Impeccable command launcher/detector were unavailable; source inspection, authored geometry, actual browser captures and a separate Impeccable review were used. Design records: `DESIGN.md`, `.impeccable/design.json`, `.impeccable/briefs/executive-studio.md`.

This change does not deploy or publish the application, add realtime transport, complete the full Next.js migration, change business ownership, or grant agents new execution authority.

The disposable browser fixture and regression script are saved in `scripts/studio-browser/`; follow that directory's README to reproduce acceptance without accessing any real account or database. In Vite development, React StrictMode may mount a canvas twice; cleanup deliberately disposes resources without explicitly losing the reused context.

After integration with the command center/automation work, the studio shares its guarded task-decision service: business ownership, the displayed approval fingerprint, safe action allowlist and pending-approval status must match. Other action types or outstanding revisions remain in their dedicated workflows; the studio does not introduce a broader execution path. Both the command center and automation/knowledge screens are linked from business selection and studio navigation.

## Agent focus, decisions and readability
The timeline's All events filter displays the full executive floor. The selected-agent filter hides other avatar meshes and labels and centers the camera on that department. All events restores the overview. Selection controls remain available to change department. Solo mode suppresses cross-floor paths while retaining the route card and recorded timeline; full-room mode shows the transfer between both participants.

Both clients also read the authenticated decision log (latest 500 records, via `recent=true`) independently from task/event snapshots. Initial successful decision reads establish their own baseline; request failures retain prior records and display an error. Explicit or established decision communication routes join the same animation queue. Task-backed result logs do not fabricate a second CEO assignment. Task states and non-routed decisions are still shown as timeline records. Owner revision requests point from owner to department. Existing default decision-log ordering remains unchanged; recent mode returns the newest bounded window in chronological order, scoped by existing ownership and optional run filters.

Readability now applies to both applications: 16px body/form baseline, authored small text raised to 14px, legacy small utility text raised to 14–15px, clearer navigation/secondary text, and larger chart labels. Mobile roster and activity controls wrap to accommodate readable text. No website-language switch was requested or implemented.
