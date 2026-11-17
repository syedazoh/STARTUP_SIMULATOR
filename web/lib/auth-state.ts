export function authConfigurationIssue(env: Record<string, string | undefined>): string | null {
  const url = env.NEXT_PUBLIC_SUPABASE_URL, key = env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key || /YOUR_PROJECT/i.test(url) || /^YOUR_/i.test(key))
    return "Configure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY in web/.env.local, then restart Next.js. Use the same Supabase project in backend/.env.";
  try {
    const parsed = new URL(url);
    const local = ["localhost", "127.0.0.1", "[::1]"].includes(parsed.hostname);
    if ((parsed.protocol !== "https:" && !(local && parsed.protocol === "http:")) || parsed.username || parsed.password || parsed.search || parsed.hash || !["", "/"].includes(parsed.pathname)) throw new Error();
  } catch {
    return "NEXT_PUBLIC_SUPABASE_URL must be your Supabase project HTTPS URL (or a localhost development provider), without credentials, a path or query. Restart Next.js after correcting it.";
  }
  return null;
}
export function authErrorCode(error: {status?: number; name?: string; code?: string} | null) {
  if (error?.status === 429) return "rate";
  if (error?.code === "email_not_confirmed") return "confirmation";
  if (error?.name === "AuthRetryableFetchError" || error?.status === 0 || (error?.status || 0) >= 500) return "unavailable";
  return "login";
}
export function signupDestination(hasSession: boolean) {return hasSession ? "/workspace" : "/login?notice=verify";}
export function authNotice(code?: string, signup = false) {
  if (code === "configuration") return "Authentication is not configured. Check the Supabase settings below and restart Next.js.";
  if (code === "unavailable") return "Cannot reach the authentication provider. Check the Supabase project URL and network, then retry.";
  if (code === "rate") return "Too many authentication requests. Wait a minute before retrying.";
  if (code === "confirmation") return "Confirm your email before signing in. Open the latest confirmation email and try again.";
  if (code === "input") return "Enter a valid email and a password between 8 and 128 characters.";
  return signup ? "Account creation failed. Check your details and retry." : "Sign-in failed. Check your Supabase account credentials and email confirmation. A classic-app account must be linked after Supabase sign-in.";
}
