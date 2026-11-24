# Dashboard reference adaptation — 24 November 2026

The owner supplied three compact analytics dashboard screenshots and requested the existing Startup Simulator theme. Their structure is adapted to black/purple/off-white/beige rather than copying their white/green colors or sample numbers.

## Changes
Next business workspace now has a sticky business/navigation sidebar, four existing snapshot metrics, department workload and financial bar charts, a beige owner-attention panel and clear boardroom entry. Mobile navigation scrolls internally; forms, plans, task detail/review and reports remain below the overview. Existing ad hoc top links moved into the sidebar. The approval shortcut restores All departments and navigates to the task list; only the original explicit review/approval controls can authorize execution.

Charts reuse readWorkspace and add no API requests. Task counts cover the latest 200 loaded tasks; financial values are current simulator ledger units, without invented currency or growth. Negative values plot around zero. Empty/unavailable branches retain explanations instead of placeholder curves. Dataset launch balances stay separate.

Vite retains its shell and operating controls, elevates recorded-history charts ahead of simulation controls, uses department accents consistently and adds the same plum/beige hierarchy. History curves no longer animate a partial reveal on each poll. No real-time or performance claim follows from this visual change.

## Verified
- Next production build/type checking and 27 unit tests pass.
- Vite lint, 63 unit tests and production build pass. Existing mixed static/dynamic Three imports and large-bundle warnings remain.
- `web/tests/dashboard-theme.browser.cjs`: real Next authentication/business route against `scripts/studio-browser/fixture.py` on localhost only. Verifies loaded financial snapshot, department form, inbox navigation without approval, explicit exact-action approval against the disposable fixture and widths 320/390/768/1100/1440px. No page errors. No production credentials/database/provider used.
- `web/tests/dashboard-vite.browser.cjs`: all API requests intercepted with local synthetic history/read responses; widths 320/390/768/1100/1440px; no page errors or business writes. Static `/src/api` module requests are explicitly excluded from the API interception.
- Captures: `/tmp/dashboard-reference/{next,vite}-{width}.png`. Inline review found/fixed mobile sidebar min-content overflow and low-contrast attention-panel metadata, then confirmed the corrections. This is not an independent reviewer endorsement or WCAG certification.

Actual historical dashboard performance, physical Safari/iOS, all unavailable-data combinations and production Supabase permissions were not revalidated by these visual tests. Backend authorization/execution source is unchanged. No environment publication, deployment, billing or live communication.
