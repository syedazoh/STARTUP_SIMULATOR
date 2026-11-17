import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
const actions = readFileSync(new URL("../app/workspace/[businessId]/boardroom/actions.ts", import.meta.url), "utf8");
const studio = readFileSync(new URL("../components/studio/studio.tsx", import.meta.url), "utf8");
test("Next.js studio loads durable backend boardroom activity", () => {
  assert.match(actions, /\/events\/boardroom\?limit=100/);
});
test("Next.js studio renders recorded task objectives in activity", () => {
  assert.match(studio, /e\.data\?\.title/);
});
