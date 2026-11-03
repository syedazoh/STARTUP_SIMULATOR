# Next.js + Supabase authentication milestone

This is an additive authentication preview in `web/`, not a replacement for all existing Vite department screens. Existing frontend at port 5173 and native login remain available. The new app at port 3000 lists owned businesses; business creation and department route migration remain future work. No live account verification or deployment is claimed.

## Local setup (PowerShell)
1. Pull the integration branch/commit, then keep backend/.env's working Atlas settings.
2. Add to backend/.env:
   ```dotenv
   SUPABASE_URL=https://YOUR_PROJECT.supabase.co
   SUPABASE_PUBLISHABLE_KEY=YOUR_PUBLISHABLE_KEY
   ```
   Use your own project URL and publishable key. No Supabase secret/service-role key is needed. Restart Uvicorn from backend/. No CORS changes are needed: Next.js calls FastAPI server-to-server.
3. From repository root:
   ```powershell
   cd web
   Copy-Item .env.example .env.local
   ```
   Only copy if .env.local does not exist. Edit it with your own URL/publishable key, `BACKEND_URL=http://127.0.0.1:8000`, `APP_URL=http://localhost:3000`.
4. In Supabase Authentication settings enable Email signup and email confirmation. Site URL: http://localhost:3000. Add redirects http://localhost:3000/auth/callback and http://localhost:3000/auth/confirm.
5. Install and start:
   ```powershell
   npm ci --ignore-scripts
   npm run dev
   ```
6. Visit http://localhost:3000/signup. Register, open the confirmation email in the same browser, then sign in. If using a token-hash confirmation template, use `{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=email`. Standard PKCE confirmation uses the callback route. Provider email limits/delivery require live checking.

## Existing accounts
Create/confirm the Supabase account using your original email. After Supabase login, expand **Link existing account** and enter your ORIGINAL application email/password. Backend validates both identities, then associates the Supabase subject with the original user_id. Existing businesses, role and encryption key stay attached to that user. Matching email alone never links ownership. Do not delete/recreate existing users as a migration shortcut. If an identity was already provisioned independently, merging requires a separately reviewed operator process.

## Manual acceptance
- Signup → email confirmation → login → private business list → refresh → logout → protected page rejects access.
- Existing account → explicit link → original businesses still listed after restart.
- Invalid credentials, wrong project key, provider outage and email conflict show failure; another user's businesses remain inaccessible.
- Inspect cookies: HttpOnly, SameSite=Lax and Secure under production HTTPS. No tokens in browser localStorage or client-side API requests. Next Server Actions enforce same-origin mutation checks; do not weaken them.
- Tokens are checked with the configured Supabase /auth/v1/user endpoint. Application roles are read from MongoDB, never user-editable provider metadata. Provider outage fails closed with 503. This adds a provider round trip per authenticated API call; measure before introducing a bounded verification cache.

## Release / rollback
Keep existing native auth until live migration checks pass. Configure production APP_URL, Supabase redirect allowlist, secrets and HTTPS before deployment. This milestone is not Docker-wired into the current frontend service. Staging deployment and remaining screens are separate tasks. Rollback: revert this commit, keep MongoDB users/businesses and encrypted data unchanged; mapping collection can remain unused. Existing signup/login is retained during the transition.

## Sources
https://supabase.com/docs/guides/auth/server-side/creating-a-client
https://supabase.com/docs/reference/javascript/auth-getuser
https://supabase.com/docs/guides/auth/redirect-urls
