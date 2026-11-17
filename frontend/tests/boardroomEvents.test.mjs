import test from "node:test";
import assert from "node:assert/strict";
import {
  resolveMessage,
  getLatestMessage,
  observedMessages,
} from "../src/components/boardroom/eventRoutes.js";

test("routes marketing budget request to finance without inventing message data", () => {
  const event = {
    event_id: "e1",
    source: "marketing",
    event_type: "budget_request",
    data: { amount: 500 },
  };
  assert.deepEqual(resolveMessage(event), {
    id: "e1",
    sender: "marketing",
    receiver: "finance",
    type: "budget_request",
  });
});

test("routes finance arbitration requests to CEO", () => {
  assert.equal(
    resolveMessage({
      event_id: "e2",
      source: "finance",
      event_type: "arbitration_request",
      data: {},
    }).receiver,
    "ceo",
  );
});

test("ignores externally published or unknown events", () => {
  assert.equal(
    resolveMessage({
      event_id: "e3",
      source: "api",
      event_type: "campaign_launch",
      data: {},
    }),
    null,
  );
  assert.equal(
    resolveMessage({
      event_id: "e4",
      source: "system",
      event_type: "kpi_updated",
      data: {},
    }),
    null,
  );
});

test("accepts explicit sender and receiver on structured events", () => {
  assert.deepEqual(
    resolveMessage({
      event_id: "e5",
      sender: "hr",
      receiver: "ceo",
      event_type: "agent.message",
    }),
    { id: "e5", sender: "hr", receiver: "ceo", type: "agent.message" },
  );
});

test("latest event is not assumed to be a conversation", () => {
  const events = [
    {
      event_id: "e1",
      source: "marketing",
      event_type: "budget_request",
      data: {},
    },
    { event_id: "e2", source: "system", event_type: "kpi_updated", data: {} },
  ];
  assert.equal(getLatestMessage(events).id, "e1");
});

test("normalizes real Python agent instance IDs", () => {
  assert.equal(
    resolveMessage({
      event_id: "e6",
      source: "marketing_001",
      event_type: "budget_request",
      data: {},
    }).sender,
    "marketing",
  );
  assert.equal(
    resolveMessage({
      event_id: "e7",
      source: "finance_001",
      event_type: "arbitration_request",
      data: {},
    }).receiver,
    "ceo",
  );
  assert.equal(
    resolveMessage({
      event_id: "e8",
      source: "ceo_agent",
      event_type: "arbitration_result",
      data: {},
    }).sender,
    "ceo",
  );
});

test("all directed executive pairs are supported when explicitly recorded", () => {
  const agents = ["ceo", "finance", "marketing", "hr", "operations"];
  const events = agents.flatMap((sender) =>
    agents
      .filter((receiver) => receiver !== sender)
      .map((receiver) => ({
        event_id: `${sender}-${receiver}`,
        sender,
        receiver,
        event_type: "task_handoff",
        data: { message: `${sender} task for ${receiver}` },
      })),
  );
  assert.equal(observedMessages(new Set(), events).length, 20);
  assert.deepEqual(observedMessages(null, events), []);
  assert.deepEqual(
    observedMessages(new Set(events.map((e) => e.event_id)), events),
    [],
  );
  assert.equal(
    observedMessages(new Set(), events)[3].title,
    events[3].data.message,
  );
});
test("batched events preserve HR and Operations handoffs instead of only the latest", () => {
  const events = [
    {
      event_id: "old",
      sender: "ceo",
      receiver: "finance",
      event_type: "task_handoff",
    },
    {
      event_id: "hr",
      sender: "hr",
      receiver: "operations",
      event_type: "task_handoff",
    },
    {
      event_id: "ops",
      sender: "operations",
      receiver: "ceo",
      event_type: "task_handoff",
    },
  ];
  assert.deepEqual(
    observedMessages(new Set(["old"]), events).map((e) => e.id),
    ["hr", "ops"],
  );
});
test("subscription routes use recorded agent senders and reject external and self routes", () => {
  for (const [source, type, receiver] of [
    ["operations", "recruitment_request", "hr"],
    ["hr", "resource_request", "operations"],
    ["ceo", "campaign_launch", "marketing"],
    ["hr", "budget_request", "finance"],
  ]) {
    assert.equal(
      resolveMessage({ event_id: type, event_type: type, source }).receiver,
      receiver,
    );
    assert.equal(
      resolveMessage({ event_id: type, event_type: type, source }).sender,
      source,
    );
  }
  assert.equal(
    resolveMessage({
      event_id: "external",
      source: "manual",
      event_type: "recruitment_request",
    }),
    null,
  );
  assert.equal(
    resolveMessage({
      event_id: "self",
      source: "hr",
      event_type: "recruitment_request",
    }),
    null,
  );
});
test("business UUID and Mongo agent instance sources normalize without accepting arbitrary suffixes", () => {
  for (const source of [
    "hr_11111111-1111-4111-8111-111111111111",
    "hr_507f1f77bcf86cd799439011",
  ])
    assert.equal(
      resolveMessage({
        event_id: source,
        source,
        event_type: "resource_request",
      }).sender,
      "hr",
    );
  assert.equal(
    resolveMessage({
      event_id: "bad",
      source: "hr_foreign",
      event_type: "resource_request",
    }),
    null,
  );
});

test("durable CEO delegation displays the assigned task objective", () => {
  const [handoff] = observedMessages(new Set(), [{
    event_id: "durable-1", event_type: "task_assigned",
    sender: "ceo", receiver: "hr", source: "ceo",
    data: { title: "Recruit a designer", task_id: "task-1" },
  }]);
  assert.equal(handoff.sender, "ceo");
  assert.equal(handoff.receiver, "hr");
  assert.equal(handoff.title, "Recruit a designer");
});
test("decision records never create fictional directed messages", () => {
  assert.deepEqual(observedMessages(new Set(), [{
    event_id: "decision-1", event_type: "decision_recorded",
    source: "system", data: { title: "Decision recorded: campaign launch" },
  }]), []);
});
