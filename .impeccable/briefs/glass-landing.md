# Glass landing — guided executive introduction

Mode: Persuade, with an interactive 3D product introduction.
User request: redesign the landing page with glassmorphism, 3D executives explaining themselves one by one, light/dark toggle matching phones/browser themes, audio, popups and sliding interaction. User confirmed English voice + visible captions.

Direction: extend the established purple/off-white/beige executive world into a translucent public arrival screen. Keep the existing procedural robot assets. Large editorial invitation beside an interactive executive floor; a horizontal introduction/player panel below; a restrained process explanation and account CTA close. On phones, put the 3D artifact directly after the headline. The signature interaction is a user-started narrated spotlight tour across five departments with matching captions and a sliding role description. A user-triggered native overview dialog carries the popup request without unsolicited interruption.

Implementation: code-led, no raster comp or generated assets. Impeccable launcher is absent; existing product/design context and craft-floor were read directly. Both Next.js and Vite use one shared React introduction component and shared Three.js renderer. Each app owns matching landing CSS because their PostCSS configurations differ. Existing signup/login routes and Vite authenticated redirect remain.

Palette: dark #100a1e / off-white #f8f1ff / lavender #d7baff; light #f3eef8 / ink #291b3c / purple #67408e. Glass fill dark rgba(43,29,65,.57), light rgba(255,255,255,.51); 24px blur with opaque fallback. Self-hosted Manrope. Headline up to82px, body16–17px, compact controls/captions14px. No theme changes to authenticated workspaces.

Functional truth: public demonstration only; no tasks, approvals, communications or spend. Speech uses browser synthesis, never auto-starts on entry, and retains captions when voice is unavailable. Actual device voice quality/availability varies. Tour is a live 3D visual presentation, not an exported/prerecorded video. Respect reduced motion, hidden tabs, offscreen rendering, storage-disabled browsers and unavailable WebGL. Theme follows OS until manually set, remembers the choice, updates browser theme-color/color-scheme and renderer clear color/lights/fog/materials.

Quality bar: first viewport explains the product and exposes real 3D; all five departments reachable without audio; no horizontal overflow at320–1600px; keyboard controls and Escape dialog exit; no unsolicited audio or account mutations; themes have readable text; navigation and registration destinations match each app.

## Cinematic extension — 24 November 2026
User authorized implementation after the two reference prompts and proposal. Proceeded with the stated landing-only, cinematic product direction; no replacement stack or paid-plan promises. Phase 1 reuses the existing floor, profiles and audio, adds a stronger editorial hero, sticky navigation, explicit motion preference, synthetic-recording entry and Free/Planned sections. `/getting-started` is a public walkthrough; running the existing synthetic scenario remains account/business scoped.

THESIS: Make the path from startup direction to owner decision legible before account creation.
OWN-WORLD: Existing Executive Studio, near-black/purple and warm beige, self-hosted Manrope, genuine procedural 3D. Light mode retains readable dark text on warm pale glass.
STORY: Invitation and floor → existing agent player → workflow explanation → demo recording → free demo account/future plans.
FIRST VIEWPORT: Readable large invitation, executive floor and demo action on desktop; phones stack the floor immediately after the headline.
FORM: Code-led extension of the existing glass landing, pinned to the user-supplied references and established brand. Launcher unavailable; no concept roll/comp or independent review claimed.

Phase 2 implemented: selectable expanded agent chapters and a nine-step synthetic launch handoff walkthrough, including all five departments and a separate owner station. Commercial entitlements/paid billing remain a separate undecided scope.

## Requested libraries — 24 November 2026
Owner clarified Vengence UI (vengenceui.com) and Augment Code (augmentcode.com). Augment is not a UI library; no connection or use is claimed. Adapted Vengence staggerText and Skiper legacy ExpandedTabs with MIT notices; current Skiper website was blocked from this environment, so the specific legacy source and limitations are documented. Framer Motion imports belong to each app; shared UI receives app-owned primitives. Source/license notices ship with both public builds. Synthetic walkthrough selection never calls backend/provider APIs.
