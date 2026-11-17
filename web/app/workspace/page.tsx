import { redirect } from "next/navigation";
import { supabase } from "../../lib/supabase";
import { backend } from "../../lib/backend";
import { logout, linkAccount } from "../actions";
import CreateBusiness from "./create-business";
import { Submit } from "../../components/submit";
export const dynamic = "force-dynamic";
type Business = { id: string; company_name: string; industry: string };
export default async function Workspace({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const client = await supabase();
  const {
    data: { user },
    error,
  } = await client.auth.getUser();
  if (error || !user) redirect("/login");
  const params = await searchParams;
  let businesses: Business[] = [];
  let issue = "";
  try {
    await backend("/api/auth/me");
    businesses = await backend("/api/businesses");
  } catch (e) {
    issue = e instanceof Error ? e.message : "Workspace unavailable";
  }
  return (
    <>
      <section className="hero compact">
        <p className="eyebrow">Your owner workspace</p>
        <h1>Welcome back.</h1>
        <p>{user.email}</p>
        <form action={logout}>
          <Submit>Sign out</Submit>
        </form>
      </section>
      <section className="card"><h2>New to your executive workspace?</h2><p>See how to create a business, propose a plan, review approvals and follow the result.</p><a href="/getting-started">Watch the product demo &amp; quick start →</a></section>
      {params.error && (
        <p role="alert" className="error">
          The action failed. Check original account credentials or retry.
        </p>
      )}
      <section className="card">
        <h2>Your businesses</h2>
        {issue ? (
          <>
            <p role="alert" className="error">
              {issue}
            </p>
            <a href="/workspace">Retry connection</a>
          </>
        ) : businesses.length ? (
          <ul className="workspace-businesses">
            {businesses.map((b) => (
              <li key={b.id}>
                <a href={`/workspace/${b.id}`}>
                  <strong>{b.company_name}</strong>
                </a>
                <small>{b.industry}</small>
                <a className="button" href={`/workspace/${b.id}/boardroom`}>
                  Enter executive studio
                </a>
                <a className="button secondary" href={`/workspace/${b.id}`}>
                  Command center
                </a>
                <a href={`/workspace/${b.id}/automation`}>
                  Automation &amp; knowledge
                </a>
                {" · "}
                <a href={`/workspace/${b.id}/demo`}>Synthetic launch demo</a>
              </li>
            ))}
          </ul>
        ) : (
          <p>No businesses yet. Create your first workspace below.</p>
        )}
      </section>
      {!issue && <CreateBusiness />}
      <details className="card">
        <summary>Link existing account</summary>
        <p>
          Enter your original Startup Simulator login to retain business
          ownership and encrypted credentials.
        </p>
        <form action={linkAccount}>
          <label htmlFor="old-email">Original email</label>
          <input
            id="old-email"
            name="email"
            type="email"
            defaultValue={user.email}
            autoComplete="username"
            required
          />
          <label htmlFor="old-password">Original password</label>
          <input
            id="old-password"
            name="password"
            type="password"
            autoComplete="current-password"
            minLength={8}
            maxLength={128}
            required
          />
          <Submit>Link my existing account</Submit>
        </form>
      </details>
    </>
  );
}
