import Link from "next/link";
import { authConfigurationIssue, authNotice } from "../../lib/auth-state";
import { signup } from "../actions";
import { Submit } from "../../components/submit";
export default async function Signup({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const params = await searchParams;
  const configuration = authConfigurationIssue(process.env);
  return (
    <section className="card">
      <p className="eyebrow">Start with your identity</p>
      <h1>Create your account</h1>
      <p>
        Use your existing Startup Simulator email if you plan to link your
        business data.
      </p>
      {params.error && (
        <p role="alert" className="error">
          {authNotice(params.error, true)}
        </p>
      )}
      {configuration && <p role="alert" className="error">{configuration}</p>}
      {!configuration && <form action={signup}>
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
          autoComplete="new-password"
          minLength={8}
          maxLength={128}
          required
        />
        <small>At least 8 characters. Choose a unique password.</small>
        <Submit>Create account</Submit>
      </form>}
      <p>
        <Link href="/login">Return to sign in</Link>
      </p>
    </section>
  );
}
