"use server";
import { backend } from "../../../../lib/backend";

// Return expected failures explicitly: production Server Actions redact thrown errors.
async function safely(action: () => Promise<unknown>) {
  try {
    return { ok: true as const, data: await action() };
  } catch (error) {
    return {
      ok: false as const,
      error:
        error instanceof Error
          ? error.message
          : "Request failed. Please retry.",
    };
  }
}
export async function demoRead(businessId: string) {
  return safely(() =>
    backend(`/api/businesses/${encodeURIComponent(businessId)}/demo`),
  );
}
export async function demoImport(businessId: string, form: FormData) {
  return safely(() =>
    backend(`/api/businesses/${encodeURIComponent(businessId)}/demo/imports`, {
      method: "POST",
      body: form,
    }),
  );
}
export async function demoCommand(
  businessId: string,
  importId: string,
  command: "launch" | "reset-preview" | "reset",
  payload: unknown = {},
) {
  return safely(async () => {
    const base = `/api/businesses/${encodeURIComponent(businessId)}/demo/${encodeURIComponent(importId)}`;
    if (command === "reset-preview") return backend(`${base}/reset`);
    if (!["launch", "reset"].includes(command))
      throw new Error("Unknown command");
    return backend(`${base}/${command}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  });
}
export async function demoDecision(
  taskId: string,
  decision: "approve" | "reject",
) {
  return safely(async () => {
    if (!["approve", "reject"].includes(decision))
      throw new Error("Unknown decision");
    return backend(`/api/tasks/${encodeURIComponent(taskId)}/${decision}`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  });
}
