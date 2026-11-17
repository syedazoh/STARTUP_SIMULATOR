# Startup Simulator
<!-- impeccable:product-schema 1 -->

## Platform
web

## Users
Business owners supervise five departments: CEO, Finance, Marketing, HR and Operations. This is an existing simulation and approval workspace.

## Product Purpose
Set a direction, inspect proposed work, approve actions and review persisted outcomes. Visual collaboration must explain recorded business state rather than invent agent conversations.

## Operating Context
Next.js `web/` is the current authenticated migration workspace; React/Vite `frontend/` contains the existing full application. FastAPI owns authentication/authorization, tasks and execution. Supabase identity and MongoDB business ownership are preserved. Both frontends must remain usable.

## Capabilities and Constraints
The backend exposes polling-based tasks, events and agent snapshots. Task approval can execute an action immediately. CEO review and owner authorization are separate. The dataset launch is a synthetic deterministic scenario. Live provider readiness and deployment are not established by visual tests.

## Brand Commitments
User explicitly requested a fully visual 3D frontend: black and purple gradients, hints of off-white/beige, visible avatars sending and receiving tasks. This replaces the older emerald identity for the targeted frontends.

## Evidence on Hand
Existing task/event APIs, shared synthetic sample dataset and approval routes. New visual preview must stay labelled synthetic and must never create or execute tasks. No Figma file or callable Figma tools were available in this session.

## Product Principles
- Keep the owner in control of approval.
- Use persisted task state as truth.
- Explain missing data honestly.
- Preserve a usable non-3D alternative.
