"use server";
import { redirect } from "next/navigation";
import { supabase } from "../lib/supabase";
function fields(form: FormData) {
  const email = String(form.get("email") || "").trim(),
    password = String(form.get("password") || "");
  if (
    !email ||
    email.length > 254 ||
    password.length < 8 ||
    password.length > 128
  )
    redirect("/login?error=input");
  return { email, password };
}
export async function login(form: FormData) {
  const client = await supabase();
  const { error } = await client.auth.signInWithPassword(fields(form));
  if (error) redirect("/login?error=login");
  redirect("/workspace");
}
export async function signup(form: FormData) {
  const client = await supabase();
  const { error } = await client.auth.signUp({
    ...fields(form),
    options: {
      emailRedirectTo: `${process.env.APP_URL || "http://localhost:3000"}/auth/callback`,
    },
  });
  if (error) redirect("/signup?error=signup");
  redirect("/login?notice=verify");
}
export async function logout() {
  const client = await supabase();
  const { error } = await client.auth.signOut();
  if (error) redirect("/workspace?error=logout");
  redirect("/login");
}
export async function linkAccount(form: FormData) {
  const client = await supabase();
  const {
    data: { user },
    error,
  } = await client.auth.getUser();
  if (error || !user) redirect("/login");
  const {
    data: { session },
  } = await client.auth.getSession();
  if (!session) redirect("/login");
  const url = process.env.BACKEND_URL || "http://127.0.0.1:8000";
  const credentials = fields(form);
  let linked = false;
  try {
    const res = await fetch(`${url}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
      cache: "no-store",
      signal: AbortSignal.timeout(12000),
    });
    if (res.ok) {
      const native = await res.json();
      try {
        const result = await fetch(`${url}/api/auth/link-supabase`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${native.access_token}`,
          },
          body: JSON.stringify({ access_token: session.access_token }),
          cache: "no-store",
          signal: AbortSignal.timeout(12000),
        });
        linked = result.ok;
      } finally {
        await fetch(`${url}/api/auth/logout`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${native.access_token}`,
            "X-Requested-With": "XMLHttpRequest",
          },
          signal: AbortSignal.timeout(12000),
        });
      }
    }
  } catch {
    linked = false;
  }
  redirect(linked ? "/workspace" : "/workspace?error=link");
}
