# Cinematic landing: phase 1 evidence

24 November 2026. Public landing only; shared Next.js and Vite implementation. The owner authorized work after the proposal; implementation used the stated cinematic/public-first defaults. No paid entitlement, checkout, anonymous simulator or deployment was added.

## Implemented
- Editorial invitation and shared 3D floor with the existing five selectable agents, English narration and captions.
- Sticky glass navigation, theme control and persisted Motion on/off. OS reduced motion takes precedence, renderer RAF stops when disabled, and narration no longer automatically advances agents when motion is off.
- Free-demo entry leading to the existing public captioned recording/quick start, plus account creation through each app's existing route.
- Free demo simulation presentation and clearly Planned future offering without invented prices or feature limits.
- Storage-blocked Vite startup regression repaired separately; tokens remain memory-only.

## Verification
- Next: `npm run typecheck`, 27 unit tests and production build passed.
- Vite: lint, 63 unit tests and production build passed. Existing warnings remain: mixed static/dynamic Three/scene imports and the large main bundle (about 1.52 MB minified, 424 KB gzip). No performance improvement is claimed.
- Browser: `node web/tests/landing.browser.cjs` against the Next production server; also `LANDING_BASE_URL=http://127.0.0.1:5173 ...` against Vite. Both passed 320, 390, 768, 1100 and 1440px in dark/light; no horizontal overflow. Checked persistent preferences, live OS reduced-motion changes, department selection with motion off, demo/signup routes, overview/Escape, and combined storage/WebGL/voice-unavailable fallback. Normal public pages produced no page errors or mutation requests during these checks.
- Captures: `/tmp/cinematic-landing/{dark,light}-{320,390,768,1100,1440}.png`; Vite equivalents in `/tmp/cinematic-landing-vite`. Captures are local review evidence, not production telemetry.
- Actual device Safari/iOS, assistive-technology certification, real speech quality and performance benchmarks were not tested. Public browser checks do not validate Supabase account creation or the backend launch scenario anew.

## Inline finish review
The finishing review and design-documentation roles were performed inline; this is not an independent reviewer endorsement. Launcher unavailable; no generated comp or concept-roll result is claimed. Scope is this first slice, not the full reference prompts.

Disposition: ship (phase 1 scope).

### Persistence
PRODUCT.md retains business truth. DESIGN.md and the existing publicLanding sidecar extension describe the observed palette, type and motion behavior. The surface brief records the implementation contract and later phase boundary.

### Fidelity
| Element | Assessment | Evidence/authority |
| --- | --- | --- |
| Type | Match | Existing self-hosted Manrope; larger readable editorial heading; phone reflow visible in captures. |
| Material | Match | Actual shared Three.js robots and scene; themed glass over an uncluttered ground. |
| Ground | Match | Near-black/purple and warm off-white/beige identity; readable pale theme. |
| Hero and 3D | Match | Large invitation beside the floor on desktop; floor directly below heading on phones. |
| Free demo | Adaptation | Reuses public walkthrough and existing account-scoped workflow; does not invent anonymous execution. |
| Future plans | Adaptation | Owner supplied Free only; other offerings marked Planned rather than fabricated. |
| Portfolio/desert content | Adaptation | Excluded because the product is a supervised startup simulation, not a portfolio or compute company. |

### Ceiling
Richer scroll chapters and the explicit synthetic handoff walkthrough remain phase 2; this phase preserves the functioning introductions and recording. No claim of reproducing the complete reference sites.

### Material fixes
None remaining within phase 1's inspected Chromium layouts and controls. The storage-disabled startup failure was fixed and verified. Existing Vite bundle warnings remain a separate optimization concern.

### Keep
Preserve readable business text, authentic 3D, non-3D/audio alternatives, synthetic labels and human approval boundaries in later phases.

## Next phase
Add richer agent chapters and the explicit synthetic product-launch handoff walkthrough. Agree commercial plan names, prices, quotas and entitlements before building paid subscriptions. Signed-in UI remains unchanged by this phase.
