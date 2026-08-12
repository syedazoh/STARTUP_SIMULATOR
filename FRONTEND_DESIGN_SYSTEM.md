# Frontend Design System — "Enterprise Cyber-Minimalism"

This is the exact visual specification for the entire frontend. Every screen should be built from these tokens — no ad hoc colors, spacing, or type sizes outside what's defined here. Where a screen isn't explicitly covered below, derive it from these same tokens rather than improvising a new style.

---

## 1. Design Concept

**Subject:** a command console for autonomous AI agents running a business — the feeling should be closer to a mission-control room or a trading terminal than a typical SaaS dashboard. The owner is *supervising* something alive, not filling out forms.

**Signature element:** the **live agent communication terminal** on the dashboard — a monospaced, real-time streaming log of agents talking to each other (`[10:42:01] [CEO_AGENT → FINANCE_AGENT]: ...`). This is the one place the product shows its own machinery, and it should be treated as the visual anchor of the whole app: every other screen is calmer than this one on purpose, so the terminal keeps its charge.

---

## 2. Color Tokens

| Token | Hex | Use |
|---|---|---|
| `--bg-base` | `#0B0E14` | App background (Deep Charcoal) |
| `--bg-surface` | `#161B22` | Cards, panels, modals |
| `--bg-surface-raised` | `#1C222B` | Hover/active state of a surface, dropdowns |
| `--border` | `#21262D` | All borders, dividers, table lines |
| `--accent-primary` | `#00F0FF` | Electric Cyan — primary actions, active states, focus rings, links |
| `--accent-positive` | `#00FF87` | Neon Emerald — positive metrics, "active/running" status, approvals |
| `--accent-negative` | `#FF3B30` | Neon Crimson — alerts, errors, rejections, "paused/failed" status |
| `--text-primary` | `#E6EDF3` | Headings, primary body text |
| `--text-muted` | `#8B949E` | Slate Gray — secondary text, labels, timestamps, placeholder text |
| `--text-disabled` | `#4A5058` | Disabled controls |

**Rule:** cyan is for *action and focus*, emerald/crimson are for *status only* (never used for buttons or nav — reserved so a glance at emerald/crimson always means "something happened," not "click here"). Do not introduce a second accent hue anywhere in the product.

---

## 3. Typography

| Role | Face | Weight/Size guidance |
|---|---|---|
| Display / page titles | Inter (or SF Pro Display where available) | 600–700 weight, 28–36px, tight letter-spacing (-0.01em) |
| UI body / labels / buttons | Inter | 400–500 weight, 13–15px |
| Agent logs, JSON payloads, code, IDs, timestamps | JetBrains Mono | 400 weight, 12–13px, `--text-muted` unless it's the active line |

**Type scale:** `12 / 13 / 14 / 16 / 20 / 24 / 32px`. Don't introduce sizes outside this scale.
**Line height:** 1.5 for body copy, 1.2 for display headings, 1.6 for terminal/log lines (logs need breathing room to stay scannable at speed).

---

## 4. Layout & Spacing

- **Spacing scale (px):** `4, 8, 12, 16, 24, 32, 48, 64` — all margins/padding/gaps come from this scale only.
- **Border radius:** `6px` for buttons/inputs, `10px` for cards/panels, `4px` for small badges/pills. No fully rounded (pill) buttons — the aesthetic is precise, not soft.
- **Grid:** 12-column, 24px gutter on desktop (≥1280px); collapses to a single column with 16px gutter below 768px.
- **Elevation:** this theme uses **borders, not shadows**, to separate surfaces — a card is `--bg-surface` on `--bg-base` with a 1px `--border` outline. Reserve a soft shadow (`0 8px 24px rgba(0,0,0,0.4)`) only for floating elements (modals, dropdowns) that need to visually lift off the page.

---

## 5. Component Specs

**Buttons**
- Primary: `--accent-primary` background, `#0B0E14` text (dark text on bright cyan for contrast), 6px radius, 500 weight label, subtle glow on hover (`box-shadow: 0 0 12px rgba(0,240,255,0.35)`).
- Secondary: transparent background, 1px `--border`, `--text-primary` label, border brightens to `--accent-primary` on hover.
- Destructive (reject/revoke): 1px `--accent-negative` border, `--accent-negative` text, fills solid on hover.
- Disabled: `--text-disabled` text, `--border` background, no hover state.

**Cards / panels**
- `--bg-surface`, 1px `--border`, 10px radius, 24px internal padding (16px on mobile).
- A card's top-right corner is the conventional home for a status badge (see below) — keep this consistent everywhere a card represents something with state (a task, an agent, a business).

**Status badges/pills**
- 4px radius, 12px monospace text, uppercase, letter-spacing 0.05em.
- Running/Active/Approved → emerald text on `rgba(0,255,135,0.1)` background.
- Paused/Pending → `--text-muted` text on `rgba(139,148,166,0.1)` background.
- Failed/Rejected/Alert → crimson text on `rgba(255,59,48,0.1)` background.

**Inputs**
- `--bg-base` fill, 1px `--border`, 6px radius, `--text-primary` value text, `--text-muted` placeholder.
- Focus: border becomes `--accent-primary`, plus a 2px cyan focus ring offset outward (this doubles as the accessibility focus indicator — never remove it, never rely on color alone).

**Terminal / log feed (the signature element)**
- `--bg-base` (slightly darker than surrounding cards, to read as "a screen within the screen"), JetBrains Mono, 13px, 1.6 line height.
- Each line prefixed with a dim timestamp (`--text-muted`), then `[AGENT_NAME]` in a per-agent color chip (see agent color mapping below), then the message in `--text-primary`.
- New lines animate in with a quick fade + 4px upward slide (150ms) — this is the one place continuous motion is welcome; everywhere else, motion should be purposeful and brief (see §6).

**Charts (Recharts)**
- Line/area strokes in `--accent-primary` and `--accent-positive` for the dual-axis revenue/burn chart; grid lines in `--border` at low opacity; axis labels in `--text-muted`, JetBrains Mono for numeric ticks.

**Per-agent color mapping** (used consistently across terminal, tabs, badges, chat)
- CEO/Strategy → `--accent-primary` (cyan)
- Finance → `--accent-positive` (emerald)
- Marketing → `#B39CFF` (a single added violet, reserved *only* for Marketing's identity — not a general accent)
- Operations/Support → `#FFB454` (amber, reserved only for Operations)
- HR → `--text-primary` neutral white-gray

---

## 6. Motion (Framer Motion)

- Page transitions: 150–200ms fade + 8px slide, ease-out. No bouncy/spring easing anywhere — this theme is precise, not playful.
- Modals: scale from 0.97→1 + fade, 150ms.
- Button/card hover: 100ms color/border transition only, no scale-on-hover (scale reads as "consumer app," not "console").
- Task-queue item resolving (approved/rejected): a brief 200ms flash of the relevant status color across the card border before it animates out of the list — this is the one micro-interaction worth spending polish on, since it's the moment the owner's decision visibly takes effect.
- Respect `prefers-reduced-motion`: fall back to instant state changes, no slides/fades, for anyone with that OS setting on.

---

## 7. Page-by-Page Layout Notes

**`/login`, `/register`** — split screen, 50/50 on desktop (stacks on mobile). Left: abstract glowing node network (SVG, animated slowly, cyan nodes/edges on `--bg-base`) representing the LangGraph agent graph — this is thematic foreshadowing of the dashboard's terminal, not decoration. Right: centered auth form, max-width 380px, "Launch Instant Demo Sandbox" as a secondary/ghost button below the primary form. Bottom-left corner: small `--text-muted` status pill, "AWS Cloud Node Status: ● ONLINE" (emerald dot).

**`/dashboard`**
```
┌─────────────────────────────────────────────────────────┐
│ [Startup Name]   Day 14   $Running Cost   ●WS  Pause Export│
├───────────┬───────────┬───────────┬───────────┬─────────┤
│ Revenue   │ Burn Rate │ Runway    │ Sentiment │ Users   │  ← KPI cards, equal width
├───────────┴───────────┴───────────┴───────────┴─────────┤
│  Revenue vs Burn (dual-axis line chart)                  │
├───────────────────────────┬───────────────────────────────┤
│  Agent Terminal (mono,     │  Task Queue                  │
│  scrollable, filter chips) │  (pending approvals, cards)  │
├───────────────────────────┴───────────────────────────────┤
│  Event Injector (row of quick-action buttons)             │
└─────────────────────────────────────────────────────────┘
```
Terminal and Task Queue sit side by side on desktop (roughly 60/40 split) since they're the two things an owner checks together — "what happened" and "what needs me."

**`/agents/[agent-id]`**
```
┌─────────────────────────────────────────────────────────┐
│ ← Back    [Agent Name]     [Mode: Manual ⇄ Auto]         │
├───────────────────────────┬───────────────────────────────┤
│  Agent-specific workspace  │  Chat panel                  │
│  (goal tree / P&L / CSAT   │  (persistent, collapsible)   │
│  / campaigns, per agent)   │                               │
└───────────────────────────┴───────────────────────────────┘
```
The chat panel is always docked right, collapsible but never a modal — chatting with an agent should feel like a persistent side-conversation, not an interruption.

**`/admin/businesses`** — plain dense data table (JetBrains Mono for IDs/numbers, Inter for names), no charts, no color beyond status badges. Deliberately less "alive" than the owner dashboard — admin is oversight, not command.

**`/memory-inspector`** — search bar (cyan focus ring) at top; results as a list of cards, each showing distance score as a small numeric badge, agent color chip, timestamp, and a monospace text snippet — visually this page borrows the terminal's monospace language since it's also "reading the machine's memory."

---

## 8. Accessibility Floor (non-negotiable regardless of theme)
- All interactive elements have a visible focus ring (the cyan ring defined in §5), never removed via `outline: none` without a replacement.
- Color is never the only signal — status badges carry text labels, not just color.
- Minimum contrast: `--text-primary` on `--bg-base`/`--bg-surface` meets WCAG AA; verify `--text-muted` does too at the sizes it's used for (bump to 14px minimum if a muted label fails at 12px).
- Fully responsive down to 375px width; the dashboard's two-column terminal/queue split stacks vertically on mobile, terminal first.
