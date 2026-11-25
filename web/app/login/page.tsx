import {redirect} from "next/navigation";
import {supabase} from "../../lib/supabase";
import {cookies} from "next/headers";
import EmailLogin from "./email-login";
import {safeReturnTo} from "../../lib/login-flow";
import Link from "next/link";
import { authConfigurationIssue, authNotice } from "../../lib/auth-state";
import { login } from "../actions";
import { Submit } from "../../components/submit";
export default async function Login({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const params = await searchParams;
  const pending=(await cookies()).get("startup-pending-email")?.value||"";
  const configuration = authConfigurationIssue(process.env);
  let signedIn=false;
  if(!configuration){try{const client=await supabase();const {data:{user}}=await client.auth.getUser();signedIn=!!user}catch{}}
  if(signedIn)redirect(safeReturnTo(params.next));
  return (
    <section className="card">
      <p className="eyebrow">Welcome back</p>
      <h1>Sign in to your workspace</h1>
      <p>
        Use your existing Supabase email. Enter the code here to return to your business. Original native accounts may need a one-time ownership link.
      </p>
      {params.error && (
        <p role="alert" className="error">
          {authNotice(params.error)}
        </p>
      )}
      {params.notice === "verify" && (
        <p role="status" className="notice">
          Check your email to confirm your account, then sign in here.
        </p>
      )}
      {configuration && <p role="alert" className="error">{configuration}</p>}
      {!configuration&&<EmailLogin initialEmail={pending} next={safeReturnTo(params.next)}/>}
      {!configuration&&<details open={params.method==="password"}><summary>Use Supabase password instead</summary><form action={login}>
        <input type="hidden" name="next" value={safeReturnTo(params.next)}/>
        <label htmlFor="email">Email address</label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          maxLength={254}
          required
        />
        <label htmlFor="password">Password</label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          minLength={8}
          maxLength={128}
          required
        />
        <Submit>Sign in</Submit>
      </form></details>}
      <p>
        New here? <Link href="/signup">Create account</Link>
      </p>
    </section>
  );
}
