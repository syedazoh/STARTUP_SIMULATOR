import "server-only";
import { supabase } from "./supabase";
export async function backend(path: "/api/auth/me" | "/api/businesses") {
  const client = await supabase();
  const {
    data: { user },
    error,
  } = await client.auth.getUser();
  if (error || !user)
    throw new Error("Your session ended. Please sign in again.");
  const {
    data: { session },
  } = await client.auth.getSession();
  if (!session) throw new Error("Please sign in again.");
  const res = await fetch(
    `${process.env.BACKEND_URL || "http://127.0.0.1:8000"}${path}`,
    {
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "X-Auth-Provider": "supabase",
      },
      cache: "no-store",
      signal: AbortSignal.timeout(12000),
    },
  );
  if (!res.ok)
    throw new Error(
      res.status === 409
        ? "Existing account found. Link your original login below to preserve your businesses."
        : "Workspace unavailable. Check backend/Supabase configuration, then retry.",
    );
  return res.json();
}
