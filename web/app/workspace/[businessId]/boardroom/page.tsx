import { backend } from "../../../../lib/backend";
import { loadStudio } from "./actions";
import Studio from "../../../../components/studio/studio";
export default async function Boardroom({
  params,
}: {
  params: Promise<{ businessId: string }>;
}) {
  const { businessId } = await params;
  const business = await backend(
    `/api/businesses/${encodeURIComponent(businessId)}`,
  );
  const snapshot = await loadStudio(businessId);
  return (
    <Studio
      key={businessId}
      businessId={businessId}
      name={business.company_name}
      initial={snapshot}
    />
  );
}
