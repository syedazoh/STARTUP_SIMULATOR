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
