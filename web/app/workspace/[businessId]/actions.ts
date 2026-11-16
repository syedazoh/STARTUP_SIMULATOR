"use server";
import { backend } from "../../../lib/backend";
import {
  departmentCommand,
  goalPayload,
  requireDecision,
  type Task,
  type Workspace,
  type Panel,
} from "../../../lib/workspace-contracts";
async function safely<T>(action: () => Promise<T>) {
  try {
    return { ok: true as const, data: await action() };
  } catch (e) {
    return {
      ok: false as const,
      error:
        e instanceof Error
          ? e.message
          : "Request failed. Refresh before retrying.",
    };
  }
}
const base = (id: string) => `/api/businesses/${encodeURIComponent(id)}`;
export async function readWorkspace(businessId: string): Promise<Workspace> {
  const root = base(businessId);
  async function panel<T>(path: string, fallback: T): Promise<Panel<T>> {
    try {
      return { data: (await backend(root + path)) as T };
    } catch (e) {
      return {
        data: fallback,
        error: e instanceof Error ? e.message : "Section unavailable",
      };
    }
  }
  const [tasks, agents, plans, reports, finances] = await Promise.all([
    panel<Workspace["tasks"]["data"]>("/tasks?limit=200", []),
    panel<Workspace["agents"]["data"]>("/agents", {}),
    panel<Workspace["plans"]["data"]>("/ceo/plans", []),
    panel<Workspace["reports"]["data"]>("/ceo/reports", []),
    panel<Workspace["finances"]["data"]>("/finances", null),
  ]);
  return { tasks, agents, plans, reports, finances };
}
export async function proposeWork(
  businessId: string,
  department: string,
  form: FormData,
) {
  return safely(async () => {
    const command = departmentCommand(department, form);
    return backend(`${base(businessId)}/agents/${command.path}`, {
      method: "POST",
      body: JSON.stringify(command.payload),
      signal: AbortSignal.timeout(90000),
    });
  });
}
export async function proposePlan(businessId: string, form: FormData) {
  return safely(() =>
    backend(`${base(businessId)}/ceo/plans`, {
      method: "POST",
      body: JSON.stringify(goalPayload(form)),
      signal: AbortSignal.timeout(90000),
    }),
  );
}
export async function activatePlan(businessId: string, planId: string) {
  return safely(() =>
    backend(
      `${base(businessId)}/ceo/plans/${encodeURIComponent(planId)}/activate`,
      { method: "POST", signal: AbortSignal.timeout(90000) },
    ),
  );
}
export async function decideTask(
  businessId: string,
  taskId: string,
  decision: "approve" | "reject",
  feedback: string,
  expectedFingerprint: string,
) {
  return safely(async () => {
    const task: Task = await backend(
      `/api/tasks/${encodeURIComponent(taskId)}`,
    );
    requireDecision(task, businessId, decision);
    if (
      !expectedFingerprint ||
      task.approval_fingerprint !== expectedFingerprint
    )
      throw new Error(
        "Proposal changed since your preview. Refresh and review again.",
      );
    if (typeof feedback !== "string" || feedback.length > 2000)
      throw new Error("Feedback must be at most 2000 characters.");
    return backend(`/api/tasks/${encodeURIComponent(taskId)}/${decision}`, {
      method: "POST",
      body: JSON.stringify({
        owner_feedback: feedback,
        expected_fingerprint: expectedFingerprint,
      }),
      signal: AbortSignal.timeout(90000),
    });
  });
}
