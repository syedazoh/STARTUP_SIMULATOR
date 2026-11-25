# One entry point — 25 November 2026

Open **http://localhost:3000**. The documented `cd web; npm run dev` serves Next.js. The historical `cd frontend; npm run dev` serves Vite at 5173. Before this change these used independent Supabase and native-password sessions. The native session did not restore a Supabase login, return paths were discarded, and an unlinked identity correctly received an ownership conflict rather than another user's business. None of these findings establishes the state of the owner's private Windows configuration.

## Existing account

1. Start MongoDB and FastAPI with the original database URL and database name. Preserve `.env` values. Require `/health` to report Mongo connected.
2. Start `web` and open localhost:3000/login. Enter the existing Supabase email, request the sign-in code and enter the latest code on the same screen. Requesting a code uses `shouldCreateUser: false`: it is not registration.
3. A protected `next` path returns to that business page; otherwise a single existing business opens directly. Multiple businesses use the company selector.
4. If an original native account has not been linked, use the existing one-time Link existing account form. It requires the original native password and the same verified Supabase email. Matching email alone never grants ownership. Do not create a replacement company or database.
5. An explicit Supabase password fallback remains on the same retained page. Registration stays at /signup.

## Exact Supabase operator settings

Use the **existing** project on both frontend and backend:
- Supabase Dashboard → Authentication → Sign In / Providers → Email: enable email sign-in.
- Authentication → Email Templates → **Magic Link**: include `{{ .Token }}` in the message body so `signInWithOtp` supplies a code the user can enter. A template containing only a confirmation link does not provide the same-screen code experience. Preserve normal account-confirmation templates/verification.
- Authentication → URL Configuration: Site URL `http://localhost:3000`; allow the configured `/auth/callback` and `/auth/confirm` URLs. Use your HTTPS origin when deployed.
- Confirm email delivery/SMTP and provider rate limits. Do not disable email confirmation to hide a delivery problem. The UI handles resend/expired/invalid codes; the provider enforces authoritative limits.

`web/.env.local`: NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY, BACKEND_URL, APP_URL. Backend uses matching SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY, plus the original MONGODB_URL/MONGODB_DB_NAME. Never expose the service-role key in browser variables.

No real keys, email addresses or codes are required in chat. This checkout had no usable Supabase configuration and no FastAPI listener during the initial safe check. Live email delivery, the owner's original database and their account link therefore remain unverified.

## Retained classic pages without another login

Vite /login and /register now lead to the canonical Next sign-in/registration. A missing native session can POST through Vite's `/api/auth/legacy-session` proxy to Next. Next validates its HttpOnly Supabase session, requires the configured classic Origin and custom request header, then calls the existing backend identity mapper to create a revocable native session. No password, code or token is placed in a URL or browser storage. Access tokens remain in the existing in-memory client; refresh stays HttpOnly. The bridge does not bypass original ownership linking.

Local defaults use the same hostname, **localhost**, on ports 3000 and 5173. Mixing localhost and 127.0.0.1 prevents shared-host cookies. Set CLASSIC_APP_URL on Next and MAIN_APP_PROXY_TARGET/VITE_MAIN_APP_URL on Vite if changing the local addresses. The bridge is not a general cross-domain SSO service. Current release packaging serves Next as the main app; separately hosted classic domains need an explicit later authentication design.

Refresh cookies move from `/api/auth` to `/`; the old scoped cookie is expired during rotation. SameSite Strict, HttpOnly, secure-in-production and request-origin checks remain. This lets sign-out revoke both sessions. Next logout and classic logout use the same cleanup; failures remain visible rather than falsely reporting complete sign-out. Theme preferences are not removed by logout.
