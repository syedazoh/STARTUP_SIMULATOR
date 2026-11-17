import { backend } from "../../../lib/backend";
import { readWorkspace } from "./actions";
import CommandCenter from "./command-center";
import type { Business } from "../../../lib/workspace-contracts";
export const dynamic = "force-dynamic";
export default async function BusinessWorkspace({
  params,
}: {
  params: Promise<{ businessId: string }>;
}) {
  const { businessId } = await params;
  let business: Business;
  try {
    business = await backend(
      `/api/businesses/${encodeURIComponent(businessId)}`,
    );
  } catch (e) {
    return (
      <section className="card">
        <a href="/workspace">← Businesses</a>
        <h1>Workspace unavailable</h1>
        <p role="alert" className="error">
          {e instanceof Error ? e.message : "Could not load business."}
        </p>
        <a href={`/workspace/${encodeURIComponent(businessId)}`}>
          Retry connection
        </a>
      </section>
    );
  }
  return (
    <>
      <p><a href="/getting-started">Product demo &amp; quick start →</a></p>
      <p>
        <a href={`/workspace/${encodeURIComponent(businessId)}/automation`}>
          Jobs, deadlines, knowledge &amp; MCP →
        </a>
      </p>
      <CommandCenter
        business={business}
        initial={await readWorkspace(businessId)}
      />
    </>
  );
}
