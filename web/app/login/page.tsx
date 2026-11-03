import Link from "next/link";
import { login } from "../actions";
import { Submit } from "../../components/submit";
export default async function Login({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const params = await searchParams;
  return (
    <section className="card">
      <p className="eyebrow">Welcome back</p>
      <h1>Sign in to your workspace</h1>
      <p>
        Use your Supabase account. Existing users can link their original login
        after signing in.
      </p>
      {params.error && (
        <p role="alert" className="error">
          Sign-in failed. Check your credentials and email confirmation, then
          retry.
        </p>
      )}
      {params.notice === "verify" && (
        <p role="status" className="notice">
          Check your email to confirm your account, then sign in here.
        </p>
      )}
      <form action={login}>
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
      </form>
      <p>
        New here? <Link href="/signup">Create account</Link>
      </p>
    </section>
  );
}
