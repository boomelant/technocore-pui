import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const workflow = readFileSync(new URL("../workflows/pui-agent.ts", import.meta.url), "utf8");
const route = readFileSync(new URL("../app/api/agent/start/route.ts", import.meta.url), "utf8");

test("durable PUI workflow uses a versioned symbol", () => {
  assert.match(workflow, /export async function puiAgentWorkflowV4\(/);
  assert.doesNotMatch(workflow, /export async function puiAgentWorkflow\(/);
});

test("start route can only launch the v4 workflow", () => {
  assert.match(route, /import \{ puiAgentWorkflowV4 \}/);
  assert.match(route, /start\(puiAgentWorkflowV4, \[holder\]\)/);
  assert.match(route, /workflow: "puiAgentWorkflowV4"/);
  assert.doesNotMatch(route, /start\(puiAgentWorkflow,/);
});
