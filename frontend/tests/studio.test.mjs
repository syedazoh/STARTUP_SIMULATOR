import test from "node:test";
import assert from "node:assert/strict";
import {
  observedChanges,
  taskTransfer,
  previewTransfers,
  agentId,
} from "../src/studio/model.mjs";
const pending = {
  id: "t1",
  agent: "marketing",
  status: "pending_approval",
  objective: "Launch",
};
test("first fetch never replays historical tasks", () =>
  assert.deepEqual(observedChanges(null, [pending]), []));
test("an initially empty completed fetch can observe future work", () =>
  assert.equal(observedChanges(new Map(), [pending])[0].receiver, "owner"));
test("unchanged polling cannot replay a handoff", () =>
  assert.deepEqual(
    observedChanges(new Map([["t1", pending]]), [{ ...pending }]),
    [],
  ));
test("owner approval never impersonates a CEO decision", () => {
  const transfer = taskTransfer({ ...pending, status: "executed" }, pending);
  assert.equal(transfer.sender, "owner");
  assert.equal(transfer.receiver, "marketing");
});
test("unknown agents and unrelated new executed tasks cannot invent a transfer", () => {
  assert.equal(taskTransfer({ ...pending, agent: "stranger" }), null);
  assert.equal(taskTransfer({ ...pending, status: "executed" }), null);
});
test("preview is explicit, contains all stages and changes no application state", () => {
  const data = previewTransfers();
  assert.ok(data.every((t) => t.source === "visual preview"));
  assert.ok(data.some((t) => t.status === "approved"));
  assert.ok(data.some((t) => t.receiver === "finance"));
});
test("agent IDs accept established instance forms only", () => {
  assert.equal(agentId("finance_123"), "finance");
  assert.equal(agentId("finance_foreign"), null);
});

test("mobile approval label separates from the Operations label", async () => {
  const { layoutLabels } = await import("../src/studio/model.mjs");
  const positions = {
    ceo: [245, 112],
    finance: [145, 101],
    marketing: [285, 172],
    hr: [95, 151],
    operations: [205, 205],
    owner: [195, 188],
  };
  const result = layoutLabels(positions, 354, 390);
  assert.ok(Math.abs(result.owner[1] - result.operations[1]) >= 35);
  for (const point of Object.values(result))
    assert.ok(point[0] > 0 && point[0] < 354 && point[1] >= 70);
});
test("new persisted CEO plans display delegation from CEO", () => {
  const transfer = taskTransfer({
    id: "plan-task",
    agent: "hr",
    status: "pending_ceo_review",
    source: "ceo",
    plan_id: "actual-plan",
  });
  assert.equal(transfer.sender, "ceo");
  assert.equal(transfer.receiver, "hr");
  assert.equal(transfer.label, "Task assigned");
});

test("budget delegation routes CEO to Finance, not Finance back to CEO", () => {
  const task = {
    id: "budget-assignment",
    agent: "finance",
    action_type: "budget_request",
    objective: "Review department budget",
    source: "ceo",
    plan_id: "persisted-plan",
    status: "pending_approval",
  };
  const [transfer] = observedChanges(new Map(), [task]);
  assert.equal(transfer.sender, "ceo");
  assert.equal(transfer.receiver, "finance");
  assert.equal(transfer.title, "Review department budget");
});
test("a four-department plan preserves every assignment in snapshot order", () => {
  const tasks = ["finance", "marketing", "hr", "operations"].map((agent) => ({
    id: agent,
    agent,
    source: "ceo",
    plan_id: "persisted-plan",
    status: "pending_ceo_review",
  }));
  const transfers = observedChanges(new Map(), tasks);
  assert.deepEqual(
    transfers.map((t) => t.receiver),
    ["finance", "marketing", "hr", "operations"],
  );
  assert.ok(transfers.every((t) => t.sender === "ceo"));
});
test("the visual preview starts with the requested CEO to Finance budget example", () => {
  const first = previewTransfers()[0];
  assert.equal(first.sender, "ceo");
  assert.equal(first.receiver, "finance");
  assert.match(first.title, /budget/i);
});

test("collaboration preview gives every executive sending and receiving roles", () => {
  const rows = previewTransfers();
  for (const id of ["ceo", "finance", "marketing", "hr", "operations"]) {
    assert.ok(
      rows.some((t) => t.sender === id),
      `${id} never sends`,
    );
    assert.ok(
      rows.some((t) => t.receiver === id),
      `${id} never receives`,
    );
  }
  assert.ok(
    rows.every((t) => t.source === "visual preview" && t.sender !== t.receiver),
  );
});
test("participant roles name the actual counterpart without claiming task acceptance", async () => {
  const { collaborationRoles } = await import("../src/studio/model.mjs");
  const transfer = { sender: "hr", receiver: "operations" };
  const sending = collaborationRoles(transfer, "sending");
  assert.equal(
    sending.find((a) => a.id === "hr").activity,
    "Sending to Operations",
  );
  assert.equal(
    sending.find((a) => a.id === "operations").activity,
    "Receiving from HR",
  );
  assert.equal(sending.find((a) => a.id === "ceo").direction, "idle");
  const arrived = collaborationRoles(transfer, "arrived");
  assert.equal(
    arrived.find((a) => a.id === "operations").activity,
    "Visual arrived from HR",
  );
  assert.ok(
    collaborationRoles(null, "sending").every((a) => a.direction === "idle"),
  );
});
