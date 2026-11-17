// The current EventBus publishes a source and event type, not a generic receiver.
// Only route established agent interactions; never animate unsupported claims.
const AGENTS = new Set(["ceo", "finance", "marketing", "hr", "operations"]);
export function normalizeAgent(value) {
  if (typeof value !== "string") return null;
  const id = value.toLowerCase();
  if (AGENTS.has(id)) return id;
  const prefix = id.split("_")[0];
  if (
    AGENTS.has(prefix) &&
    (/^(?:[0-9]+|[a-f0-9]{24}|[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$/.test(
      id.slice(prefix.length + 1),
    ) ||
      id === prefix + "_agent")
  )
    return prefix;
  return null;
}
const ROUTES = {
  budget_request: { sender: "marketing", receiver: "finance" },
  budget_negotiation: { sender: "finance", receiver: "marketing" },
  arbitration_request: { sender: "finance", receiver: "ceo" },
  arbitration_result: { sender: "ceo", receiver: "finance" },
};
// These receivers are the AgentManager EventBus subscriptions, not guessed roles.
const SUBSCRIBERS = {
  budget_request: "finance",
  campaign_launch: "marketing",
  recruitment_request: "hr",
  resource_request: "operations",
};
export function resolveMessage(event) {
  if (!event?.event_id) return null;
  const explicit =
    event.sender && event.receiver
      ? { sender: event.sender, receiver: event.receiver }
      : event.data?.sender && event.data?.receiver
        ? { sender: event.data.sender, receiver: event.data.receiver }
        : SUBSCRIBERS[event.event_type]
          ? {
              sender: normalizeAgent(event.source),
              receiver: SUBSCRIBERS[event.event_type],
            }
          : ROUTES[event.event_type];
  if (!explicit) return null;
  // Routes derived from event type are valid only with the expected agent source.
  if (
    !event.sender &&
    !event.data?.sender &&
    normalizeAgent(event.source) !== explicit.sender
  )
    return null;
  const sender = normalizeAgent(explicit.sender),
    receiver = normalizeAgent(explicit.receiver);
  if (!AGENTS.has(sender) || !AGENTS.has(receiver) || sender === receiver)
    return null;
  return { id: event.event_id, sender, receiver, type: event.event_type };
}
export function getLatestMessage(events) {
  if (!Array.isArray(events)) return null;
  for (let index = events.length - 1; index >= 0; index--) {
    const result = resolveMessage(events[index]);
    if (result) return result;
  }
  return null;
}

// Consume every routed event in a snapshot, preserving its recorded order.
export function observedMessages(previous, events) {
  if (previous === null) return [];
  return events.flatMap((event) => {
    if (previous.has(event.event_id)) return [];
    const route = resolveMessage(event);
    if (!route) return [];
    return [
      {
        ...route,
        label: event.event_type.replaceAll("_", " "),
        title:
          typeof event.data?.message === "string"
            ? event.data.message
            : event.event_type.replaceAll("_", " "),
        status: event.event_type,
        source: "backend",
      },
    ];
  });
}

// Persisted decisions retain their own IDs. A task result alone is not a message.
export function decisionEvents(records) {
  return records.filter(row => row._id || row.id).map(row => ({
    ...row, event_id: `decision:${row._id || row.id}`,
    // Task-backed decisions already have task transitions; avoid inventing another assignment.
    source: row.data?.task_id && !row.sender && !row.data?.sender ? 'decision_log' : row.source,
  }));
}
