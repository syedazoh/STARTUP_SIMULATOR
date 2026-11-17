"use server";
import { backend } from "../../lib/backend";
import { businessPayload } from "../../lib/workspace-contracts";
export async function createBusiness(form: FormData) {
  try {
    const business = await backend("/api/businesses", {
      method: "POST",
      body: JSON.stringify(businessPayload(form)),
    });
    return { ok: true as const, id: business.id as string };
  } catch (error) {
    return {
      ok: false as const,
      error:
        error instanceof Error ? error.message : "Could not create business.",
    };
  }
}
