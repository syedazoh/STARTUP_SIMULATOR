import "server-only";
import { createServerClient } from "@supabase/ssr";
import { authConfigurationIssue } from "./auth-state";
import { cookies } from "next/headers";
export async function supabase() {
  const jar = await cookies();
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL,
    key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  const issue = authConfigurationIssue(process.env);
  if (issue || !url || !key) throw new Error(issue || "Configure Supabase in web/.env.local");
  return createServerClient(url, key, {
    cookieOptions: {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
    },
    cookies: {
      getAll: () => jar.getAll(),
      setAll(values) {
        try {
          values.forEach(({ name, value, options }) =>
            jar.set(name, value, options),
          );
        } catch {
          /* Proxy refreshes cookies for Server Components. */
        }
      },
    },
  });
}
