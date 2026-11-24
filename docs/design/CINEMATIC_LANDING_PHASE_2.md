# Cinematic landing: chapters, references and launch handoffs

24 November 2026. Completes the public landing's second design phase; signed-in business execution, billing and deployment are outside this change.

## References actually used
- **Framer Motion**: `import {motion, AnimatePresence} from 'framer-motion'` in both app-owned landing wrappers. Version 12.23.24 supports the two existing React majors. Pin motion-dom 12.23.23 and motion-utils 12.23.6: the newer semver-compatible motion-dom selected initially removed an export used by this Framer version and broke the Next build. Both lockfiles include the verified overrides.
- **Skiper legacy ExpandedTabs**: MIT adaptation from cpiprint/legacy-skiper-ui, linked in source notices. The current Skiper website returned an environment-network 403. This is the available legacy component, not a claim to use a new or paid catalog. Department names remain visible instead of collapsing to icon-only buttons; the selected role expands. No outside-click hook, Lucide dependency or Tailwind migration was needed.
- **Vengence UI staggerText**: MIT adaptation from Ashutoshx7/VengeanceUI. Word-staggered reveal preserves visible server-rendered content, proper word spacing, one screen-reader text alternative and motion-off handling.
- The supplied **Augment Code** link identifies a coding-assistant service, not a UI library. No Augment package, account connection or claimed use was added.
- Full notices are in `frontend/src/landing/ui/THIRD_PARTY_NOTICES.md` and ship in both public directories at `/licenses/landing-ui.txt`.

## Behavior
Five chapter buttons select the existing avatar/profile/narration state. The existing audio/caption controls remain user-started and support all departments.

The separate launch walkthrough reuses the procedural boardroom renderer. Nine local explanatory steps show CEO → Marketing → Finance → HR → Operations → CEO → owner review → illustrative owner approval → simulated execution → outcome reporting, with individual explicit routes in `launch-scenario.mjs`. The owner and CEO remain distinct. Each step names sender, receiver, what is being handed over and its artifact; a bright directional line and packet connect scene participants. It shows no fabricated performance metrics.

Manual selection, previous and next work without playback. Playback starts only on a user action, advances every 5.2 seconds while in view, stops at the end and replays from step one when requested. Pausing retains the step. Hidden documents and reduced motion stop playback; motion off disables play but preserves manual exploration and static routes. WebGL failure retains every textual handoff and control. No task/provider API, approval mutation, email, post or money transfer is called by this walkthrough. All state is local and synthetic.

## Checks
- Vite lint and 64 tests passed; Next typecheck, 27 tests and production build passed. Vite production build passed. The routing test fixture now imports the real animation module rather than treating its new named imports as an unrelated default stub; existing auth assertions remain.
- Both public browser implementations passed the full behavior round and final confirmation. Final captures/tests include corrected hero word spacing, phone line break and explicitly decoded lazy poster images before full-page screenshots.
- Browser matrix: 320/390/768/1100/1440px × dark/light on both apps. Covers chapter/profile selection, direct walkthrough steps, owner review and approval routes, end/replay, timed advance, pause, manual motion-off navigation, preference persistence, live OS preference changes, demo routes, dialog/Escape and combined storage/WebGL/voice fallback.
- Motion-off regression instruments WebGL drawElements and requires zero additional draws once state settles; manual selection can still render an updated static frame.
- Public normal-flow checks require no page errors and no non-GET/HEAD requests. No credentials or real accounts used.
- Local captures: `/tmp/landing-libraries-next-final` and `/tmp/landing-libraries-vite-final`, including full-page theme/width captures and the walkthrough. They are temporary review evidence, not committed assets or production telemetry.
- Existing Vite mixed-import/large-chunk warnings remain. Main bundle is about 1.65 MB minified / 466 KB gzip after requested Framer Motion integration; this change does not claim better latency or production readiness. Physical-device Safari, screen-reader certification and performance benchmarks were not performed.

## Inline finishing review
Review/documentation were performed inline, not by an independent agent. Source, established design tokens, desktop/phone captures and fallback captures were checked. Palette and 3D material remain the existing Executive Studio; chapter controls and route text are readable and keyboard-native. The initial review found joined hero words and lazy poster captures; spacing/line break were repaired in one batch and capture preparation now loads the actual poster. No fabricated prices, entitlements or live execution claims were introduced.

Disposition: ship for this public-landing scope. Final confirmation passed on both apps, including the instrumented motion-off check and corrected captures. Commercial plan definitions, authenticated redesign, real-provider connectivity and AWS rollout remain their separately recorded work; no publication or deployment occurred.
