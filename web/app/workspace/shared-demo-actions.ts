"use server";
import { backend } from "../../lib/backend";
import { redirect } from "next/navigation";
export async function openSharedDemo() {
  let id: string;
  try {
    const result = await backend("/api/workflow-demo", {
      method: "POST",
      body: "{}",
      signal: AbortSignal.timeout(90000),
    });
    id = result.business_id;
  } catch {
    redirect("/workspace?error=demo_setup");
  }
  redirect(`/workspace/${encodeURIComponent(id)}/agents/ceo`);
}
