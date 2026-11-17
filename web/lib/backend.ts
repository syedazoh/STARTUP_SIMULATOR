import "server-only";
import { apiError } from "./api-errors";
import { supabase } from "./supabase";
export async function backend(path: string, init: RequestInit = {}) {
  if (!path.startsWith("/api/") || path.includes(".."))
    throw new Error("Invalid API path");
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
  let res: Response;
  try {
    res = await fetch(
      `${process.env.BACKEND_URL || "http://127.0.0.1:8000"}${path}`,
      {
        ...init,
        headers: {
          ...(init.body instanceof FormData
            ? {}
            : { "Content-Type": "application/json" }),
          Authorization: `Bearer ${session.access_token}`,
          "X-Auth-Provider": "supabase",
        },
        cache: "no-store",
        signal: init.signal || AbortSignal.timeout(12000),
      },
    );
  } catch {
    throw new Error(
      "Cannot reach the backend or the request timed out. Check port 8000 and refresh before retrying; submitted work may still be processing.",
    );
  }
  if (!res.ok)
    throw new Error(
      apiError(res.status, await res.json().catch(() => null), path),
    );
  return res.json();
}
