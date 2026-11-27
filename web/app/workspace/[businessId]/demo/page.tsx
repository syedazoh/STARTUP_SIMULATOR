import { backend } from "../../../../lib/backend";
import Demo from "./demo";
import RetailData from "../../../../components/retail-data";

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
      <a href={`/workspace/${encodeURIComponent(businessId)}`}>
        ← Command center
      </a>
      <section className="hero compact">
        <p className="eyebrow">Synthetic business laboratory</p>
        <h1>Data laboratory</h1>
        <p>
          Historical retail and fictional startup data stay distinct. Use the shared workspaces for the new five-agent launch.
        </p>
      </section>
      <RetailData businessId={businessId}/><Demo businessId={businessId} initial={initial} />
    </>
  );
}
