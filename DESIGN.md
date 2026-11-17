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
