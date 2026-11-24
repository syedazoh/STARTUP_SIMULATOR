# Appearance and reported team — 24 November 2026

## User-visible behavior
A persistent display rail on both frontends exposes a direct light/dark button and the native expandable Appearance panel at the top-right. It remains visible after navigation and scrolling; in the immersive boardroom it moves inside the dialog so keyboard controls remain reachable. Executive Glass keeps the purple frosted surface; Pearl Water uses reflective rippled geometry; Monolith uses a matte rectangular sculpture and restrained solid surfaces. Each works with light, dark or the device setting. The selected preset/mode/motion is stored under `startup-appearance` in this browser, not in an account or business. Legacy landing theme preference is read until a new preference is saved. Invalid/blocked storage falls back to usable defaults. Reset restores Executive Glass, device mode and decorative motion. OS reduced motion overrides animation. Motion does not authorize or execute tasks.

Public and private footers use a procedural beige faceted globe and orbit, never another agent avatar. Rendering pauses out of view/when the tab is hidden. A static geometric fallback remains if WebGL is unavailable. Background geometry continues through scrolling, behind readable controls. No new dependency or third-party asset/license was introduced.

The Next company command center has Team setup and direct role-workspace links with actual loaded review/work counts. Classic Company setup captures the same human team breakdown; Business Profile edits it. Both keep it distinct from five AI agent roles. The classic pending-review labels only count the loaded pending task list; they do not claim lifetime work totals.

## Workforce API
- Optional `workforce` on `POST /api/businesses` must match `starting_headcount` when supplied.
- `GET /api/businesses` and `GET /api/businesses/{id}` return the saved value, or null for an old business.
- Owner-authorized `PUT /api/businesses/{id}/workforce` replaces this planning context only. It does not change starting values, simulation HR state, payroll, tasks or approvals.

```json
{"total_headcount":7,"positions":[{"department":"Engineering","role":"Software engineer","count":5,"employment_type":"full_time"}]}
```

Two people in that example remain explicitly not assigned yet. Up to 50 groups; department and role are trimmed 1–100 characters. Counts are positive strict integers; total is 0–1,000,000. Sum cannot exceed total. Duplicate case-insensitive department/role/employment groups must be combined. Employment values: full_time, part_time, contract, intern, unspecified. Chat receives this under `owner_reported_team_context_not_live_hr_state`, separate from the simulation's live status. No employee names or personal records are collected.

## Verification
Focused backend workforce/business/chat tests run offline in the existing dependency image with application/tests mounted read-only and no network: 25 passed. Next unit tests: 34 passed. Classic unit tests: 63 passed, including final onboarding save/retry and workforce forwarding. Next production types/build and classic lint/build passed. Browser checks use disposable localhost identity/API or fully intercepted synthetic requests, not the owner's accounts. Appearance checks cover three presets × two themes × three widths on landing/dashboard; real avatar-free footer geometry; persistence, OS color scheme, reset, keyboard close and saved workforce. Additional regressions cover original video playback/fallbacks and classic pages/profile. Public and dashboard confirmations ran separately after visual corrections; the test clears only its disposable synthetic employee rows before saving. Computed action/notice contrast in both modes measured at least 8.15:1. Final local Next image digest: `sha256:8cc468e02f1791f6110fea28b3a3bdbe50c470ad5705a353ea3bd1f8f64beebd`; image not published.

Screenshots live in ignored local /tmp/appearance-release, /tmp/appearance-landing-regression and /tmp/dashboard-reference. Visual review was inline; no independent reviewer is claimed. Original Supabase/Mongo recovery and live provider/AWS behavior remain separate acceptance gates. Existing classic bundle-size/mixed-import warnings remain; no latency improvement is claimed.


### Continuous theme-control regression
Next browser acceptance checks all 16 public/private/error UI routes, reload persistence, top-level hit testing after scrolling, 320/390px layout and settings bounds. It also checks that closing Appearance with Escape preserves immersive mode, then a second Escape exits it. Classic browser regression checks the explicit toggle across dashboard and all five agents, plus light/dark profile. The guide, setup/admin wrappers and boardroom surfaces use the same colors. HTTP export responses and auth redirects are endpoints, not additional interactive pages. This follow-up ran no live account/provider checks or deployment.
