import { backend } from "../../../../lib/backend";
import Demo from "./demo";

export default async function DemoPage({
  params,
}: {
  params: Promise<{ businessId: string }>;
}) {
  const { businessId } = await params;
  const initial = await backend(
    `/api/businesses/${encodeURIComponent(businessId)}/demo`,
  );
  return (
    <>
      <a href="/workspace">← Businesses</a>
      <section className="hero compact">
        <p className="eyebrow">Synthetic business laboratory</p>
        <h1>Product launch</h1>
        <p>
          One shared dataset. Five department reviews. Your approval before
          simulated execution.
        </p>
      </section>
      <Demo businessId={businessId} initial={initial} />
    </>
  );
}
