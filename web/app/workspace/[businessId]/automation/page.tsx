import Automation from "./panel";
import { readAutomation } from "./actions";
import { backend } from "../../../../lib/backend";
export const dynamic = "force-dynamic";
export default async function Page({
  params,
}: {
  params: Promise<{ businessId: string }>;
}) {
  const { businessId } = await params;
  try {
    const business = await backend(
      `/api/businesses/${encodeURIComponent(businessId)}`,
    );
    return (
      <Automation
        businessId={businessId}
        departments={business.enabled_agents}
        initial={await readAutomation(businessId)}
      />
    );
  } catch (e) {
    return (
      <section className="card">
        <h1>Automation unavailable</h1>
        <p role="alert">{e instanceof Error ? e.message : "Sign in again"}</p>
        <a href="/workspace">Businesses</a>
      </section>
    );
  }
}
