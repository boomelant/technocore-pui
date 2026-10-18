import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const workflow = readFileSync(new URL("../workflows/pui-agent.ts", import.meta.url), "utf8");
const route = readFileSync(new URL("../app/api/agent/start/route.ts", import.meta.url), "utf8");

test("durable PUI workflow uses a versioned symbol", () => {
  assert.match(workflow, /export async function puiAgentWorkflowV5\(/);
  assert.doesNotMatch(workflow, /export async function puiAgentWorkflow\(/);
});

test("start route can only launch the v5 workflow", () => {
  assert.match(route, /import \{ puiAgentWorkflowV5 \}/);
  assert.match(route, /start\(puiAgentWorkflowV5, \[holder\]\)/);
  assert.match(route, /workflow: "puiAgentWorkflowV5"/);
  assert.doesNotMatch(route, /start\(puiAgentWorkflow,/);
});

test("resident v5 colocates and registers every invoked workflow step", () => {
  for (const step of [
    "acquireLeaseStep",
    "publishLifecycleStatusStep",
    "bootstrapIdentityStep",
    "observeAndDecideStep",
    "postReplyStep",
  ]) {
    assert.match(workflow, new RegExp("async function " + step + "\\("));
    assert.match(workflow, new RegExp("async function " + step + "\\([\\s\\S]*?\\{\\n  \"use step\";"));
  }
});
