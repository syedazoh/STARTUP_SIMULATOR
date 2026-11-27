"use client";
import Retail from "../../frontend/src/workflow/RetailData";
import { readRetail, uploadRetail } from "../app/workspace/retail-actions";
export default function RetailData({ businessId }: { businessId: string }) {
  return (
    <Retail businessId={businessId} read={readRetail} upload={uploadRetail} />
  );
}
