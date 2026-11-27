"use server";
import { backend } from "../../lib/backend";
const root = (id: string) => `/api/businesses/${encodeURIComponent(id)}/retail`;
export async function readRetail(id: string) {
  try {
    return { ok: true as const, data: await backend(root(id)) };
  } catch (error) {
    return {
      ok: false as const,
      error:
        error instanceof Error ? error.message : "Retail data unavailable.",
    };
  }
}
export async function uploadRetail(id: string, action: string, form: FormData) {
  try {
    if (!["preview", "import"].includes(action))
      throw new Error("Unknown import action");
    return {
      ok: true as const,
      data: await backend(root(id) + "/" + action, {
        method: "POST",
        body: form,
      }),
    };
  } catch (error) {
    return {
      ok: false as const,
      error:
        error instanceof Error ? error.message : "Import could not finish.",
    };
  }
}
