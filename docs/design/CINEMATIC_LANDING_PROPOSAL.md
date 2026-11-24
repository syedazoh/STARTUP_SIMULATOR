# Cinematic landing proposal

Status: phases 1–2 implemented, 24 November 2026, after the owner said “start working on it.” Used the stated default: public landing first and cinematic product direction. Commercial entitlements remain unimplemented.

## Objective
Turn Startup Simulator's public arrival into an immersive, understandable introduction that guides visitors toward a free demo simulation, then explains the path to future plans. Keep the established black/purple/warm off-white identity and existing light theme.

## Reference interpretation
The supplied MONOLITH prompt contributes a cinematic product narrative, a dominant hero artifact, deliberate section transitions, glass controls, and a clear route to plans. Its fictional compute business, desert assets, randomly increasing metrics, customer names and prices do not belong to this product.

The supplied portfolio prompt contributes readable editorial typography, agent chapters, an accessible motion switch, diagrams showing directional work, native mobile scrolling and accessible detail dialogs. Portfolio projects, biographies, contact details, endorsements and the prescribed replacement stack do not belong to this product.

Use the existing Next/Vite shared landing and Three.js renderer. Preserve working auth routes and the visitor-started English narration/captions. No new animation dependency is necessary for the initial slice.

## Visitor journey and proposed composition
1. **Arrival:** a large readable invitation, “Your idea. A team to move it forward.” beside a purple-lit executive floor. Primary action: “Explore the free demo.” Secondary: “Meet the agents.” Navigation links to Team, How it works and Plans; Sign in, theme and motion controls remain visible. Avoid an artificial loading gate.
2. **The team:** CEO, Finance, Marketing, HR and Operations form selectable chapters. Each chapter has a role, a concrete responsibility, an illustrative handoff and user-started English narration with captions. Preserve all controls without audio or WebGL. Desktop can use a sticky scene beside the chapters; phones use stacked content and explicit agent tabs.
3. **One launch, explained:** an explicitly synthetic walkthrough of launch brief → Marketing proposal → Finance review → owner approval → simulated execution → CEO report. Draw directional paths between the departments involved; owner approval remains a separate human step. Clicking a step reveals its explanation. This public illustration does not produce real tasks or imply recorded business events.
4. **Start with the free demo:** explain the synthetic dataset, proposal review and simulated outcomes. Distinguish an explanatory preview from a runnable account-scoped simulation. Reuse existing getting-started material and authenticated demo workflow. Confirm the desired account requirement before creating a new anonymous execution path.
5. **Plans:** lead with “Free — demo simulation.” Further plan names, amounts, quotas, integrations and availability are undecided. Present future options only as “Planned”; no checkout, fabricated discounts, disabled pretend purchase buttons or unimplemented entitlement promises. Commercial launch requires a separately agreed feature/price matrix and backend enforcement.
6. **Closing:** one clear action to begin the selected demo/onboarding path, plus Sign in. Reinforce that the owner reviews actions and that simulation outcomes are synthetic.

## Visual and interaction contract
- Persuade mode for the public landing; signed-in task screens retain their Operate hierarchy.
- Large warm typography over near-black; purple light and beige details connect the page to the boardroom. Light mode uses pale surfaces and dark readable text rather than inverted low-contrast glass.
- The 3D floor is the primary artifact. Transparent decoration stays behind opaque-enough reading surfaces; moving geometry does not compete with captions.
- Motion supports chapter changes and directed handoffs. No scroll hijacking, pointer-only functionality or mandatory long pinning on phones.
- Motion off and OS reduced motion stop ambient movement and auto-cycling. Audio remains an independent, explicitly started control.
- Real HTML headings, text and links remain visible without animation. Agent selection works with keyboard and without WebGL. All dialogs retain focus, Escape and return-focus behavior.
- Stop offscreen/hidden-tab rendering. Keep self-hosted fonts, lazy Three loading and existing renderer ownership. Do not infer performance from appearance.

## Implementation phases
1. Public hero, navigation, accessible motion control and free-demo entry. Verify both shared consumers, themes and phone layouts; report before expanding.
2. Agent chapters and synthetic handoff walkthrough, reusing narration and 3D models.
3. Plans presentation after plan definitions are settled; paid subscriptions are a separate functional scope.
4. Only after the public direction is confirmed, consider applying selected visual details to signed-in screens while preserving legibility, task state and approval controls.

## Verification planned
Check 320, 390, 768, 1100 and 1440px; dark/light; reduced motion and explicit motion off; keyboard navigation; speech unavailable; WebGL unavailable; storage blocked; hidden/offscreen behavior. Run applicable Next tests/types/build and Vite lint/tests/build. Confirm public preview makes no task/provider mutations. These checks have not been run for this proposal because no UI was changed.

## Decisions still needed
- Current slice: public landing only, cinematic product composition. Agent chapters and the synthetic walkthrough are implemented; signed-in redesign remains outside this landing scope.
- Later: free demo account requirement; paid plan names, prices, quotas and actual entitlements. None are invented here.

## Inspected evidence
PRODUCT.md; DESIGN.md; .impeccable/briefs/glass-landing.md; docs/PRD.md; docs/architecture.md; docs/designsystem.md; docs/WORKFLOWS.md; docs/RAG_PLAN.md; tasks/todo.md; frontend/src/landing/LandingExperience.jsx; frontend/src/landing/landing.css; frontend/src/pages/Landing.jsx; web/components/landing/landing.tsx; web/app/page.tsx; web/app/getting-started/page.tsx; web/app/workspace/[businessId]/demo; frontend/tests/landing.test.mjs. This is targeted design discovery, not a repository-wide capability audit.
