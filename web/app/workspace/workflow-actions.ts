"use server";
import { backend } from "../../lib/backend";
import { agentRole } from "../../lib/agent-tools-contracts";
const root = (id: string) => `/api/businesses/${encodeURIComponent(id)}`;
export async function readWorkflow(businessId: string, role: string) {
  try {
    const base = root(businessId) + "/workflow";
    const [conversation, launch, images] = await Promise.all([
      backend(`${base}/${agentRole(role)}/conversation`),
      backend(base + "/launch/state"),
      backend(`${base}/${agentRole(role)}/images`),
    ]);
    return { ok: true as const, data: { conversation, launch, images } };
  } catch (error) {
    return {
      ok: false as const,
      error:
        error instanceof Error ? error.message : "Saved workflow unavailable.",
    };
  }
}
export async function workflowCommand(
  businessId: string,
  role: string,
  command: string,
  payload: Record<string, unknown>,
  id = "",
) {
  try {
    const base = root(businessId),
      agent = agentRole(role),
      target = encodeURIComponent(id),
      paths: Record<string, string> = {
        turn: `${base}/workflow/${agent}/turns`,
        draft: `${base}/workflow/${agent}/drafts`,
        image: `${base}/workflow/${agent}/images`,
        plan: `${base}/workflow/launch/plans`,
        activate: `${base}/workflow/launch/plans/${target}/activate`,
        submit: `${base}/workflow/launch/tasks/${target}/submit`,
        approve: `/api/tasks/${target}/approve`,
        changes: `/api/tasks/${target}/request-changes`,
        reject: `/api/tasks/${target}/reject`,
        retry: `${base}/jobs/${target}/retry`,
      };
    if (!Object.hasOwn(paths, command))
      throw new Error("Unknown workflow command");
    return {
      ok: true as const,
      data: await backend(paths[command], {
        method: "POST",
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(90000),
      }),
    };
  } catch (error) {
    return {
      ok: false as const,
      error:
        error instanceof Error
          ? error.message
          : "Workflow action could not finish. Refresh before retrying.",
    };
  }
}
