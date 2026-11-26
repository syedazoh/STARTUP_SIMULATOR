import {workspaceIssue} from "../../lib/account-link";
import { redirect } from "next/navigation";
import {ACCESS_COOKIE,nativeUser} from "../../lib/native-session";
import {cookies} from "next/headers";
import { backend } from "../../lib/backend";
import { logout } from "../actions";
import CreateBusiness from "./create-business";
import { Submit } from "../../components/submit";
export const dynamic = "force-dynamic";
type Business = { id: string; company_name: string; industry: string };
export default async function Workspace({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  let user;try{user=await nativeUser((await cookies()).get(ACCESS_COOKIE)?.value)}catch{ return <section className="card"><h1>Account service unavailable</h1><p role="alert">Check FastAPI and your original MongoDB connection, then retry.</p><a href="/workspace">Retry</a></section> }
  if(!user)redirect('/login');
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
        <p>{user.email}</p><p>This is your company selector. Open an existing company’s command center or choose one of its agent workspaces below. You do not need a new project for each department.</p>
        <form action={logout}>
          <Submit>Sign out</Submit>
        </form>
      </section>
      <section className="card"><h2>New to your executive workspace?</h2><p>See how to create a business, propose a plan, review approvals and follow the result.</p><a href="/getting-started">Watch the product demo &amp; quick start →</a></section>
      {params.error && (
        <p role="alert" className="error">
          {workspaceIssue(params.error)}
        </p>
      )}
      {params.linked==="1"&&<p className="notice" role="status">Existing account linked. Your original businesses should now appear below.</p>}
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
                <div className="workspace-agent-links" aria-label={`${b.company_name} agent workspaces`}>{["ceo","finance","marketing","hr","operations"].map(role=><a key={role} href={`/workspace/${encodeURIComponent(b.id)}/agents/${role}`}>{role==="ceo"?"CEO":role==="hr"?"HR":role.charAt(0).toUpperCase()+role.slice(1)} workspace</a>)}</div>
                {" · "}
                <a href={`/workspace/${b.id}/demo`}>Synthetic launch demo</a>
              </li>
            ))}
          </ul>
        ) : (
          <p>No businesses are attached to this login yet. If you already had a company, check that the backend uses your original MongoDB database and that you signed in to the original account before creating another.</p>
        )}
      </section>
      {!issue && <CreateBusiness />}

    </>
  );
}
