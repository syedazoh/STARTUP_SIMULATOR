---
{
  "name": "Startup Simulator — Executive Studio",
  "description": "An immersive purple-lit working floor with owner-controlled approvals.",
  "colors": {
    "bg": "#0d0b12",
    "surface": "#15111d",
    "raised": "#21192b",
    "line": "#34293f",
    "text": "#f0e9df",
    "muted": "#b7a9c7",
    "purple": "#a47deb",
    "purple-deep": "#7549b4",
    "beige": "#e6d6ba",
    "button": "#a981ed",
    "button-hover": "#bb98f5",
    "button-ink": "#160d23",
    "focus": "#d9befb",
    "attention": "#dfcfb3",
    "attention-ink": "#34263b",
    "input": "#110e17",
    "input-line": "#51415f",
    "ceo": "#d9c6a4",
    "finance": "#b8a0ff",
    "marketing": "#dd98e8",
    "hr": "#e5b8a2",
    "operations": "#9eb6ed"
  },
  "typography": {
    "display": {
      "fontFamily": "Studio Sans, Inter, system-ui, sans-serif",
      "fontSize": "clamp(28px, 3vw, 41px)",
      "fontWeight": 600,
      "letterSpacing": "-0.035em"
    },
    "body": {
      "fontFamily": "Studio Sans, Inter, system-ui, sans-serif",
      "lineHeight": 1.6
    },
    "studio-body": {
      "fontSize": "14px"
    },
    "label": {
      "fontSize": "14px",
      "fontWeight": 650
    }
  },
  "rounded": {
    "input": "8px",
    "button": "10px",
    "card": "14px",
    "attention": "13px"
  },
  "spacing": {
    "small": "8px",
    "medium": "12px",
    "large": "24px",
    "card": "32px"
  },
  "components": {
    "button-primary": {
      "backgroundColor": "{colors.button}",
      "textColor": "{colors.button-ink}",
      "rounded": "{rounded.button}",
      "padding": "12px 20px",
      "height": "44px"
    },
    "button-primary-hover": {
      "backgroundColor": "{colors.button-hover}"
    },
    "input": {
      "backgroundColor": "{colors.input}",
      "textColor": "{colors.text}",
      "rounded": "{rounded.input}",
      "padding": "12px"
    },
    "card": {
      "backgroundColor": "{colors.surface}",
      "rounded": "{rounded.card}",
      "padding": "32px"
    },
    "attention": {
      "backgroundColor": "{colors.attention}",
      "textColor": "{colors.attention-ink}",
      "rounded": "{rounded.attention}",
      "padding": "21px 21px 20px"
    }
  }
}
---

# Design System: Startup Simulator

## Overview

**Creative North Star: "Executive Studio"**

A near-black working environment illuminated by purple gradients, with warm off-white text and beige reserved for human attention. The user selected visible 3D executives and task handoffs; the executive studio brief records the composition. HelloRun supplies an immersive reference, not a claim of inspected gameplay or copied assets.

The scene is a working view of persisted business state. Physical robots, terminals, receding portals and a separate owner station make collaboration spatial; readable controls and task details carry the decisions.

**Key Characteristics:**
- Purple-lit geometry against near-black surfaces.
- Small warm accents, with a prominent beige attention panel.
- Selectable avatars and equivalent list selection.
- Handoffs explain recorded changes without executing work.

## Colors

### Primary
Purple and deep purple illuminate navigation, controls and the floor. The global primary button uses its own slightly brighter purple; the studio launch control uses a darker purple gradient. Keep those observed variants distinct.

### Secondary
Beige identifies the human approval desk. The attention panel uses its own warmer paper tone with dark plum text. Warm off-white is the default reading color.

### Neutral
Near-black establishes the background; surface and raised plum separate panels. Muted lavender carries supporting text and plum lines divide dense records. The studio locally overrides the global line token with `#302738` and adds panel `#17131f`.

Agent accents map directly to the shared model: CEO is warm champagne, Finance lavender, Marketing orchid, HR peach and Operations periwinkle. Existing Vite categorical charts and status colors remain separate data semantics in `palette.js`; compatibility names such as `emerald` now resolve to purple and must not be interpreted as a new green brand.

**The Authority Rule.** Warm owner accents distinguish human approval from CEO review; color never substitutes for a task status label.

## Typography

Studio Sans is the CSS alias for self-hosted Manrope, with Inter, system-ui and sans-serif fallbacks. Both public font directories include the OFL license. The same face supplies display and body; there is no separate display-font dependency.

The studio heading uses the frontmatter display role. Its compact body is 13px, with smaller metadata and labels in existing components. Global body line height is 1.6; headings use 1.2 and slightly tightened tracking. Main marketing headlines have a separate observed clamp of 40px to 74px. Keep dense metadata secondary rather than extending its small sizes to primary instructions. Paragraphs are bounded at 72ch globally.

## Layout

The Next studio uses a 235px navigation column and a flexible main area. Main content caps at 1640px with 35px horizontal padding. Inside it, the floor and a 288px approval column are separated by 25px. The normal scene viewport is 460px high.

At 1240px the rail and gaps tighten; at 1060px the approval column moves below the floor; at 700px navigation becomes a compact horizontal row and the content stacks with 18px side padding. At 1600px the scene grows to 520px and approval column to 320px. These are observed implementation breakpoints, not a claim that every width has been visually certified.

The optional immersive dialog occupies the window, retains scene controls and status, and uses an opaque near-black backdrop. Keep its focus trap, Escape exit and return focus behavior when changing presentation.

## Elevation & Depth

Depth comes primarily from tonal surfaces, radial gradients, geometric perspective and lit Three.js materials. The themed Vite dashboard explicitly removes panel shadows. The studio is not a stack of floating shadow cards. Real robot bodies, visors, terminals, raised packet arcs and receding portals provide the signature depth.

The scene renderer is framework-neutral Three.js shared by Next/React 19 and Vite/React 18. Its model and renderer remain inside `frontend/src/studio` so the existing frontend Docker context can include them. Do not introduce a duplicate React renderer to reproduce the geometry.

Default camera movement is user drag. Optional follow tracks a handoff, and stops under reduced motion. Slow idle articulation and packet movement are suppressed under reduced motion; clearing a transfer also clears static reduced-motion packets. CSS state transitions use short durations; the global easing token is `cubic-bezier(0.16, 1, 0.3, 1)`.

## Shapes

Soft rectangular controls and panels contrast with circular station rings and angular portal geometry. Inputs use the input radius, primary buttons the button radius, and generic cards and scene frames the card radius. Studio navigation has a 9px radius; scene labels use 6px. Preserve the distinction between physical stations and overlaid HTML controls.

## Components

- **Buttons:** Global primary buttons are light purple with dark text, 12px by 20px padding and a minimum 44px height. Studio launch buttons use a deeper gradient; preview controls have plum fill and a thin border. Disabled controls dim to half opacity. Focus uses a 2px pale-purple outline with a 4px offset.
- **Fields:** Dark inset fill, plum border, warm text and 12px padding. Keep visible labels and native editing behavior.
- **Cards:** Global forms use a bounded 660px card with 32px padding, reducing to 24px on small screens. The attention panel has its own warm treatment and tighter padding.
- **Navigation:** Muted lavender links become warm-white on an active purple gradient. Team buttons and the five-column roster expose pressed selection states; roster selection stays available on mobile when the full team rail hides.
- **Status labels:** Compact plum chips support textual state. Synthetic preview labels use a warm accent and must persist while illustrative handoffs are visible.
- **Executive floor:** Five selectable robot executives surround a separate owner desk. Packets follow bright raised curves with directional arrowheads; sender gestures and receiver lighting explain the handoff. A separate high-contrast route card names the sender, receiver, task and visual phase. A five-department participant strip identifies each side of the current exchange, using plum for the sender and warm beige for the receiver; the same states highlight avatar labels. On mobile the strip wraps into three columns without crowding projected labels. The last route persists until replacement or explicit clearing. The renderer performs no network or provider effects and never writes application state. The first successful snapshot establishes the baseline without replay. Exact proposed action details precede approval controls. Animation is evidence presentation, not business authority.

## Do's and Don'ts

- Do preserve the separate owner approval station and CEO review identity.
- Do label synthetic previews throughout their display.
- Do preserve readable task details and equivalent non-3D selection.
- Do keep focus visible and stop camera follow under reduced motion.
- Don't restore emerald as the primary identity of these frontends.
- Don't animate the initial historical snapshot as new work.
- Don't treat a packet arriving as approval, execution or completion.
- Don't claim screenshots prove provider readiness or live gameplay fidelity.

Source of truth: `web/app/globals.css`, `web/components/studio/studio.css`, `frontend/src/theme/night-studio.css`, `frontend/src/theme/palette.js`, and `frontend/src/studio/{model,scene}.mjs`. This document captures source inspection; it does not certify the review screenshots, accessibility conformance, deployment or provider integrations. No Figma comp or image-generation concept was produced in this session.

### Boardroom readability update — November 17, 2026
Projected HTML labels identify departments only; the floating owner/approval-desk badge is omitted from public and authenticated views. The physical owner station and approval authority remain separate from the CEO. Department labels use 13px desktop / 12px mobile text with solid dark backgrounds and light foregrounds. Task statuses use 13px, titles 15px and identifiers 12px; the legacy inspector body uses 15px high-contrast metadata. Shared collision boxes account for the larger labels. The legacy inspector stacks below the scene at widths up to 1450px.

## Project-wide reading baseline and agent focus
Body and form text use a 16px baseline; authored compact text has a 14px floor across the public, authentication and operational surfaces. Legacy text-sm uses 15px and text-xs uses 14px. Metadata retains hierarchy through color, weight and spacing. Chart ticks/tooltips are 14px. Mobile studio rosters wrap into three columns.

The timeline filter controls scene scope: All events shows all executive avatars; the selected department shows its avatar alone with a centered camera. Other mesh groups and labels are hidden; the full floor restores on All events. Communication routes remain in readable records during solo viewing. Decision-log signals are backed by real route evidence, with a separate initial-history baseline.

## Public landing extension — glass executive introduction

This extension applies only to the public landing. Preserve the authenticated dark Executive Studio tokens, readable business records and owner approval rules above. The public composition pairs an editorial invitation with the live executive floor, a horizontal introduction/player, process explanation and account CTA. At 800px and below, the floor follows the headline before longer copy and controls. It is an illustrative introduction, not recorded business activity.

### Landing palette and glass

CSS tokens are scoped to `.launch-page` with prefix `--launch-`; light values override under `data-theme=light`.

| Token suffix | Dark | Light |
| --- | --- | --- |
| bg | `#0d0a13` | `#f4f0e9` |
| ink | `#f5efe5` | `#291e35` |
| muted | `#c6bbd3` | `#62536f` |
| glass | `rgba(35,26,48,.62)` | `rgba(255,252,248,.65)` |
| edge | `rgba(213,192,238,.24)` | `rgba(112,72,154,.24)` |
| accent | `#d7baff` | `#67408e` |
| button | `#e9d9be` | `#59327f` |
| button-ink | `#251b2e` | `#fff7ff` |
| soft | `rgba(211,175,255,.12)` | `rgba(119,77,161,.08)` |
| readable-glass | `rgba(26,19,37,.97)` | `rgba(252,248,245,.97)` |

Standard glass combines themed fill, a 1px edge, 16px radius and `blur(24px) saturate(130%)`. Unsupported backdrop filtering falls back to the opaque background token. Captions and the overview dialog use the stronger 97% alpha readable glass: moving geometry must not compete with their text. Fixed live captions explicitly disable both backdrop-filter and -webkit-backdrop-filter to avoid a black compositor rectangle over active WebGL; their tint and border remain. Other glass surfaces, including the dialog, retain blur. Agent dots preserve champagne, lavender, orchid, peach and periwinkle department identities; text and pressed state also identify selection.

### Landing type, geometry and components

`Launch Sans` is another alias for the same self-hosted Manrope (`/fonts/studio-sans.woff2`, weights 200–800), followed by Studio Sans/system fallbacks. Body is 16px/1.65, hero supporting copy 17px/1.8 (16px on phones), profile body 15px/1.8 and compact controls/captions 14px. The hero is `clamp(50px,6.2vw,92px)`, weight 550, line height 1.04 and tracking −.04em; the smallest phone override is 43px. Profile headings are 24px/1.3, growing to 26px on phones. Paragraph measure caps at 65ch.

Content caps at 1520px; the process section caps at 1320px. Page padding is `24px clamp(18px,4.5vw,80px) 0`, changing to `14px 16px 0` on phones. The hero gap is 36px (26px stacked); introduction padding is 30px by 35px, reducing to 23px on phones. Process margins reduce from 140px to 75px on phones. Responsive steps include 1600, 1150, 800, 600, 480 and 370px. The canvas is 560px high by default, 610px wide-screen, 490px compact, 460px stacked, 350px on phones and 325px on the smallest phones.

- **Navigation and actions:** Glass navigation includes the theme toggle and sign-in. Primary/secondary actions use a 12px radius, 13px by 21px padding, 14px weight-650 text and minimum 50px height. Icons have 44px circular targets; play has a 52px target. Small stage controls use a 9px radius and department tabs 8px.
- **Executive floor:** Existing procedural Three.js robots remain shared with the studio. Five labelled department buttons expose pressed selection; full-team and spotlight views are available. Loading and unavailable-WebGL copy preserve access to profiles below the canvas.
- **Sliding profile and player:** CEO, Finance, Marketing, HR and Operations each have a role, description, example and English introduction. Profile changes slide 14px over 320ms using `cubic-bezier(.16,1,.3,1)`. Previous/next, play/pause and narration controls supplement direct selection. A live caption accompanies playback and an expandable transcript remains readable without playing.
- **Overview popup:** A visitor-triggered native modal dialog has a labelled heading, close control and native Escape dismissal. No popup interrupts arrival. Readable glass carries its explanatory copy.

### Theme, motion and functional behavior

The landing follows `prefers-color-scheme` until a visitor chooses a theme. A valid `startup-landing-theme` localStorage override persists that choice; storage failure leaves the toggle usable. The component updates browser `theme-color` and root `color-scheme`, restoring prior values when unmounted. Opt-in renderer `setTheme` updates clear color, fog, lights and robot materials without changing authenticated studio defaults. The landing's IntersectionObserver calls `setVisible` for offscreen rendering. Hidden tabs and page exit stop the tour and speech.

The user starts the tour or presses play before any audio. Browser speech synthesis requests `en-US` at rate .95, introducing the five departments one by one; actual voices depend on the browser and operating system. Missing or failed speech retains captions and advances after 16 seconds. This is a live 3D tour, not prerecorded or exported video. It makes no task writes, approvals, communications or spending requests.

Focus uses a 3px accent outline with 4px offset. Labelled native controls, pressed states, a transcript and non-WebGL profiles keep the departments reachable without sound or 3D. Reduced motion disables CSS animations/transitions and smooth tour scrolling, and suppresses renderer idle animation. Phone tabs wrap; captions scroll within 38dvh and page spacing accommodates them. These are implemented behaviors, not a claim of complete accessibility certification.

Both apps render `frontend/src/landing/LandingExperience.jsx` with introductions in `agents.mjs` and the shared framework-neutral `frontend/src/studio/scene.mjs`. Landing CSS is mirrored in `frontend/src/landing/landing.css` and `web/components/landing/landing.css` because their PostCSS configurations differ. Vite retains `/register`, `/login` and its authenticated `/app` redirect; Next uses `/signup` and `/login`. The direction contract is `.impeccable/briefs/glass-landing.md`. No detector or launcher exists for this work; these tokens were documented from source, without invented tool reports.

### Cinematic public arrival — November 24, 2026

The public landing now leads with a larger editorial invitation and the shared executive floor, a horizontal introduction/player, the existing workflow explanation, a captioned-demo entry and a Free demo simulation section. A sticky readable-glass navigation exposes the team, workflow and plans on desktop, with theme, motion and sign-in controls retained on phones. The smallest width puts the wordmark on its own navigation row. Primary public actions use beige in dark mode and purple in light mode. This does not change authenticated approval semantics or introduce paid billing.

The Motion control persists `startup-landing-motion`, with OS reduced motion taking precedence and disabling the switch while active. CSS transitions and animations stop, the shared renderer cancels its animation frame through `setReducedMotion`, and the narrated introduction stops automatic department advancement. Manual department selection and opt-in narration remain available. Browser theme-color matches the public background.

The demo poster reuses the existing synthetic recording and opens `/getting-started`; account creation retains the existing app-specific registration route. Further plans are explicitly Planned without invented prices or entitlements. The free account label is product presentation, not a new anonymous execution or billing system.

### Agent chapters and launch walkthrough — November 24, 2026

Public motion uses Framer Motion 12.23.24, imported by each consuming app and passed into the shared landing to preserve React 18/19 and Docker dependency ownership. MIT-adapted Skiper legacy ExpandedTabs keeps department names visible while expanding the selected role. Vengence staggerText supplies a word-level hero reveal with visible SSR text and a single screen-reader text alternative. Source and license notices ship at `/licenses/landing-ui.txt`. Augment Code is a coding assistant, not a component dependency.

A nine-step synthetic walkthrough uses a second instance of the existing Three.js renderer, showing directional paths, moving packets, sender/receiver names, explanations and artifacts. Desktop pairs the scene with its explanation; at 800px they stack. The step index is local UI state, not a persisted task or approval. Owner review and illustrative approval remain explicitly separate. Previous/next and direct step selection work without playback, speech or WebGL. User-started playback advances every 5.2 seconds while the section is visible, stops at the last step or when hidden/reduced-motion is requested, and can replay from the beginning. Motion off cancels renderer animation and disables automatic playback while keeping manual steps available.

Chapters wrap across available width. The step list uses three columns, two at 800px and one at 480px. Walkthrough canvas height is 560px, 520px compact, 490px stacked and 380px on phones. Text remains at the public 14px compact floor. The free-demo and future-plan boundaries remain unchanged.

### User correction: video-first public demo — November 24, 2026
The public nine-step messaging walkthrough and its source module were removed at the owner's request. The earlier walkthrough description above is historical, not current UI. The authenticated boardroom and its real communication visualization remain unchanged.

The poster and “Watch the project video” now open a native modal and call play on the actual existing 62.6-second H.264 recording. Native controls support pause, seek and fullscreen; English captions remain available. Escape/Close pauses playback. A separate “Read the guide” link opens written onboarding. Playback failure exposes retry and recording download instead of pretending a guide link plays video. The recording uses synthetic data and has no audio track; it is not a new production-integrations demonstration.

Public depth now includes a true Three.js metallic torus-knot sculpture behind glass, scoped to the hero area with capped pixel ratio and approximately 30fps rendering. Motion off leaves a static frame; offscreen/hidden views skip drawing; CSS atmosphere remains without WebGL. Both dark and light themes retain a clear reading area.

## Reference-led command center — November 24, 2026

The owner’s three supplied dashboard references establish the compact-sidebar/KPI/chart/action composition; the existing Executive Studio remains the visual authority. Next’s business dashboard uses a 230px sticky sidebar, a flexible content column and a 32px gap, tightening to 200px/22px at 1200px. At 760px it becomes a single bounded column with native horizontally scrolling navigation. The site header is hidden only on this dashboard to avoid duplicate branding.

Scoped dashboard surfaces are deep plum (`#191420`), raised plum (`#241c30`), lines (`#3b2e49`), warm ink (`#f3eee6`) and readable muted lavender (`#c2b3d0`). Human attention uses beige (`#e4d4b8`) with dark plum text and an explicit action. Card radii are 12–14px. Body/compact controls remain 14–15px, headings 20–23px, metric values 25–35px and business headings 28–42px. Chart labels are HTML text at 14px, not scaled-down SVG text.

Task workload and financial snapshots are labelled as such; unknown data stays unavailable. Financial values use simulator ledger units without inventing a currency, and chart geometry supports both sides of zero. The KPI/task/report data limits remain visible. The approval inbox shortcut navigates; it does not authorize work.

Vite reuses its current app shell and charts, moves recorded-history analytics above operating controls and applies the same purple/off-white/beige hierarchy. History line animation is disabled to keep polled curves stable; the reduced-motion/3D behavior elsewhere is unchanged. The current surface brief is `.impeccable/briefs/command-center.md`.
