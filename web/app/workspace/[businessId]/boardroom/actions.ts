"use server";
import { backend } from "../../../../lib/backend";
import { decideTask } from "../actions";
import type { Snapshot } from "../../../../components/studio/types";
export async function loadStudio(businessId: string): Promise<Snapshot> {
  const base = `/api/businesses/${encodeURIComponent(businessId)}`;
  const results = await Promise.allSettled([
    backend(`${base}/tasks?limit=200`),
    backend(`${base}/agents`),
    backend(`${base}/events?limit=100`),
  ]);
  const labels = ["Tasks", "Agent status", "Activity"];
  return {
    tasks: results[0].status === "fulfilled" ? results[0].value : [],
    statuses: results[1].status === "fulfilled" ? results[1].value : {},
    events: results[2].status === "fulfilled" ? results[2].value : [],
    errors: results.flatMap((r, i) =>
      r.status === "rejected"
        ? [
            `${labels[i]} could not refresh. Check your session and backend connection.`,
          ]
        : [],
    ),
    updatedAt: new Date().toISOString(),
    tasksReady: results[0].status === "fulfilled",
  };
}
export async function decideStudioTask(
  businessId: string,
  taskId: string,
  decision: "approve" | "reject",
  expectedFingerprint: string,
) {
  const result = await decideTask(
    businessId,
    taskId,
    decision,
    "",
    expectedFingerprint,
  );
  return result.ok ? { ok: true as const, task: result.data } : result;
}
