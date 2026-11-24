"use server";
import {linkFailure} from "../lib/account-link";
import { redirect } from "next/navigation";
import { supabase } from "../lib/supabase";
import { authConfigurationIssue, authErrorCode, signupDestination } from "../lib/auth-state";
function fields(form: FormData, page = "/login") {
  const email = String(form.get("email") || "").trim(),
    password = String(form.get("password") || "");
  if (
    !email ||
    email.length > 254 ||
    password.length < 8 ||
    password.length > 128
  )
    redirect(`${page}?error=input`);
  return { email, password };
}
export async function login(form: FormData) {
  const credentials = fields(form);
  if (authConfigurationIssue(process.env)) redirect("/login?error=configuration");
  let result;
  try { const client = await supabase(); result = await client.auth.signInWithPassword(credentials); }
  catch { redirect("/login?error=unavailable"); }
  if (result.error) redirect(`/login?error=${authErrorCode(result.error)}`);
  if (!result.data.session) redirect("/login?error=login");
  redirect("/workspace");
}
export async function signup(form: FormData) {
  const credentials = fields(form, "/signup");
  if (authConfigurationIssue(process.env)) redirect("/signup?error=configuration");
  let result;
  try {
    const client = await supabase();
    result = await client.auth.signUp({...credentials, options: {emailRedirectTo: `${process.env.APP_URL || "http://localhost:3000"}/auth/callback`}});
  } catch { redirect("/signup?error=unavailable"); }
  if (result.error) redirect(`/signup?error=${authErrorCode(result.error)}`);
  redirect(signupDestination(!!result.data.session));
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
  const credentials = fields(form,"/workspace");
  let linked = false;
  let failure="link_backend";
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
        if(!linked)failure=linkFailure(result.status,"link");
      } finally {
        await fetch(`${url}/api/auth/logout`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${native.access_token}`,
            "X-Requested-With": "XMLHttpRequest",
          },
          signal: AbortSignal.timeout(12000),
        }).catch(()=>{});
      }
    }else failure=linkFailure(res.status,"login");
  } catch {
    failure="link_backend";
  }
  redirect(linked ? "/workspace?linked=1" : `/workspace?error=${failure}`);
}
