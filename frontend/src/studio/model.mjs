// Business state is authoritative. The renderer never changes approval or task state.
export const AGENTS = [
  {
    id: "ceo",
    label: "CEO",
    role: "Strategy & direction",
    color: "#d9c6a4",
    position: [0, 0, -3.2],
  },
  {
    id: "finance",
    label: "Finance",
    role: "Budgets & review",
    color: "#b8a0ff",
    position: [-3.7, 0, -1.1],
  },
  {
    id: "marketing",
    label: "Marketing",
    role: "Campaigns & growth",
    color: "#dd98e8",
    position: [3.7, 0, -1.1],
  },
  {
    id: "hr",
    label: "HR",
    role: "People & hiring",
    color: "#e5b8a2",
    position: [-2.9, 0, 2.5],
  },
  {
    id: "operations",
    label: "Operations",
    role: "Delivery & resources",
    color: "#9eb6ed",
    position: [2.9, 0, 2.5],
  },
];
export const humanize = (value) =>
  String(value || "unknown")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
export const agentId = (value) => {
  if (typeof value !== "string") return null;
  return (
    AGENTS.find(
      (a) =>
        value === a.id ||
        new RegExp(
          `^${a.id}_(agent|[0-9]+|[a-f0-9]{24}|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$`,
        ).test(value),
    )?.id || null
  );
};
const NEEDS_APPROVAL = new Set(["pending_approval", "needs_changes"]);
export const isPending = (task) => NEEDS_APPROVAL.has(task.status);
export function taskPhase(task) {
  if (isPending(task)) return "Needs your approval";
  return (
    {
      pending_ceo_review: "CEO review",
      approved: "Approved",
      auto_approved: "Policy approved",
      queued: "Queued",
      executing: "Working",
      executed: "Executed",
      verified_complete: "Verified complete",
      rejected: "Rejected",
      failed: "Failed",
      blocked: "Blocked",
      cancelled: "Cancelled",
    }[task.status] || humanize(task.status)
  );
}
export function taskTransfer(task, previous) {
  const receiver = agentId(task.agent);
  if (!receiver || !task.id || previous?.status === task.status) return null;
  const base = {
    id: `task:${task.id}:${task.status}`,
    taskId: task.id,
    title: task.objective || humanize(task.action_type),
    status: task.status,
    source: "backend",
  };
  if (!previous && task.source === "ceo" && task.plan_id && receiver !== "ceo")
    return { ...base, sender: "ceo", receiver, label: "Task assigned" };
  if (task.status === "needs_changes" && previous)
    return {...base, sender: "owner", receiver, label: "Owner requested changes"};
  if (previous?.status === "pending_ceo_review" && ["approved", "auto_approved"].includes(task.status) && task.ceo_authorized)
    return {...base, sender: "ceo", receiver, label: "CEO reviewed"};
  if (isPending(task))
    return {
      ...base,
      sender: receiver,
      receiver: "owner",
      label: "Approval requested",
    };
  if (task.status === "pending_ceo_review")
    return {
      ...base,
      sender: receiver,
      receiver: "ceo",
      label: "Review requested",
    };
  if (
    ["approved", "executing", "executed", "verified_complete"].includes(
      task.status,
    ) &&
    previous &&
    isPending(previous)
  )
    return {
      ...base,
      sender: "owner",
      receiver,
      label: task.status === "approved" ? "Owner approved" : taskPhase(task),
    };
  if (task.status === "rejected" && previous && isPending(previous))
    return { ...base, sender: "owner", receiver, label: "Owner rejected" };
  return null;
}
export function observedChanges(previous, tasks) {
  // First successful snapshot is a baseline, including an empty snapshot.
  if (previous === null) return [];
  return tasks
    .flatMap((task) => {
      const result = taskTransfer(task, previous.get(task.id));
      return result && result.sender !== result.receiver ? [result] : [];
    })
    .slice(-32);
}
// One illustrative launch meeting: each executive both sends and receives work.
export function previewTransfers() {
  return [
    ["ceo", "finance", "Task assigned", "Review department budget"],
    [
      "finance",
      "marketing",
      "Budget review",
      "Share the campaign budget limits",
    ],
    ["marketing", "hr", "Staffing request", "Plan the launch support team"],
    [
      "hr",
      "operations",
      "Staffing handoff",
      "Share the proposed staffing schedule",
    ],
    ["operations", "finance", "Cost review", "Review delivery resource costs"],
    [
      "finance",
      "ceo",
      "Review requested",
      "Present the proposed launch budget",
    ],
    [
      "ceo",
      "owner",
      "Approval requested",
      "Review the illustrative launch proposal",
    ],
    [
      "owner",
      "ceo",
      "Illustrative approval",
      "Preview only — no action authorized",
    ],
    ["ceo", "marketing", "Task assigned", "Prepare the launch campaign"],
    [
      "marketing",
      "operations",
      "Delivery handoff",
      "Coordinate the launch schedule",
    ],
    ["operations", "hr", "Readiness update", "Confirm launch support coverage"],
    ["hr", "ceo", "Team update", "Share the launch staffing plan"],
  ].map(([sender, receiver, label, title], i) => ({
    id: `preview-${i + 1}`,
    sender,
    receiver,
    label,
    title,
    status:
      sender === "owner"
        ? "approved"
        : receiver === "owner"
          ? "pending_approval"
          : "illustrative",
    source: "visual preview",
  }));
}

// These describe the visual exchange, never an inferred backend acceptance.
export function collaborationRoles(transfer, stage) {
  const name = (id) =>
    AGENTS.find((a) => a.id === id)?.label || (id === "owner" ? "Owner" : id);
  return AGENTS.map((agent) => {
    const sending = transfer?.sender === agent.id;
    const receiving = transfer?.receiver === agent.id;
    return {
      ...agent,
      direction: sending ? "sending" : receiving ? "receiving" : "idle",
      activity: sending
        ? `${stage === "arrived" ? "Sent to" : "Sending to"} ${name(transfer.receiver)}`
        : receiving
          ? `${stage === "arrived" ? "Visual arrived from" : "Receiving from"} ${name(transfer.sender)}`
          : "No active transfer",
    };
  });
}

// Keep projected controls apart without per-frame DOM measurements.
export function layoutLabels(positions, width, height) {
  const placed = [];
  const result = {};
  const entries = Object.entries(positions)
    .filter(([id]) => id !== "owner")
    .sort((a, b) => a[1][1] - b[1][1]);
  if (positions.owner) entries.push(["owner", positions.owner]);
  for (const [id, point] of entries) {
    const label = AGENTS.find((a) => a.id === id)?.label || "Approval desk";
    const w = id === "owner" ? 90 : Math.max(48, label.length * 8 + 28),
      h = id === "owner" ? (width < 550 ? 26 : 42) : 36;
    const x = Math.max(w / 2 + 8, Math.min(width - w / 2 - 8, point[0]));
    const initial = point[1] - (id === "owner" ? 25 : 0);
    let y = Math.max(70, Math.min(height - h / 2 - 12, initial));
    for (const offset of [0, -38, 38, -76, 76, -114, 114, -152, 152]) {
      const candidate = Math.max(
        70,
        Math.min(height - h / 2 - 12, initial + offset),
      );
      if (
        !placed.some(
          (b) =>
            Math.abs(x - b.x) < (w + b.w) / 2 + 7 &&
            Math.abs(candidate - b.y) < (h + b.h) / 2 + 7,
        )
      ) {
        y = candidate;
        break;
      }
    }
    placed.push({ x, y, w, h });
    result[id] = [x, y];
  }
  return result;
}
