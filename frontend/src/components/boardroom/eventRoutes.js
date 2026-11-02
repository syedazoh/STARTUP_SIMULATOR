// The current EventBus publishes a source and event type, not a generic receiver.
// Only route established agent interactions; never animate unsupported claims.
const AGENTS = new Set(['ceo', 'finance', 'marketing', 'hr', 'operations'])
export function normalizeAgent(value) {
  if (typeof value !== 'string') return null
  const id = value.toLowerCase()
  if (AGENTS.has(id)) return id
  const prefix = id.split('_')[0]
  if (AGENTS.has(prefix) && (/^\\d+$/.test(id.slice(prefix.length + 1)) || id === prefix + '_agent')) return prefix
  return null
}
const ROUTES = {
  budget_request: { sender: 'marketing', receiver: 'finance' },
  budget_negotiation: { sender: 'finance', receiver: 'marketing' },
  arbitration_request: { sender: 'finance', receiver: 'ceo' },
  arbitration_result: { sender: 'ceo', receiver: 'finance' },
}
export function resolveMessage(event) {
  if (!event?.event_id) return null
  const explicit = event.sender && event.receiver
    ? { sender: event.sender, receiver: event.receiver }
    : event.data?.sender && event.data?.receiver
      ? { sender: event.data.sender, receiver: event.data.receiver }
      : ROUTES[event.event_type]
  if (!explicit) return null
  // Routes derived from event type are valid only with the expected agent source.
  if (!event.sender && !event.data?.sender && normalizeAgent(event.source) !== explicit.sender) return null
  const sender = normalizeAgent(explicit.sender), receiver = normalizeAgent(explicit.receiver)
  if (!AGENTS.has(sender) || !AGENTS.has(receiver) || sender === receiver) return null
  return { id: event.event_id, sender, receiver, type: event.event_type }
}
export function getLatestMessage(events) {
  if (!Array.isArray(events)) return null
  for (let index = events.length - 1; index >= 0; index--) {
    const result = resolveMessage(events[index])
    if (result) return result
  }
  return null
}
