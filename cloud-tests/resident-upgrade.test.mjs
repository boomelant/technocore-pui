import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { PUI_RESIDENT_REVISION } from "../src/cloud/participation.mjs";

test("resident revision is explicit and status publishes it", () => {
  assert.equal(PUI_RESIDENT_REVISION, "active-replies-v7-free-models");
  const cycle = readFileSync(new URL("../workflows/steps/pui-cycle-v2.ts", import.meta.url), "utf8");
  assert.equal(cycle.includes("revision: PUI_RESIDENT_REVISION"), true);
});

test("authenticated start route accepts only a validated deterministic holder", () => {
  const route = readFileSync(new URL("../app/api/agent/start/route.ts", import.meta.url), "utf8");
  assert.equal(route.includes('request.headers.get("x-pui-holder")'), true);
  assert.equal(route.includes("const HOLDER = /^[a-z0-9][a-z0-9-]{0,38}$/"), true);
  assert.equal(route.includes("if (requestedHolder && !HOLDER.test(requestedHolder))"), true);
  assert.equal(route.includes("verifyGithubActionsOidc"), true);
});

test("watchdog upgrades stale resident only through exact-match CAS", () => {
  const workflow = readFileSync(new URL("../.github/workflows/technocore-activity.yml", import.meta.url), "utf8");
  assert.equal(workflow.includes("EXPECTED_REVISION: active-replies-v7-free-models"), true);
  assert.equal(workflow.includes("resident-lease"), true);
  assert.equal(workflow.includes('NEW_LEASE="${HOLDER}|${EXPIRY_MS}"'), true);
  assert.equal(workflow.includes("'if': os.environ['CURRENT']"), true);
  assert.equal(workflow.includes('if [ "$HTTP_CODE" != "409" ]'), true);
  assert.equal(workflow.includes("x-pui-holder: ${HOLDER}"), true);
  assert.equal(workflow.includes("refusing to take over malformed or foreign lease"), true);
});

test("watchdog preserves a healthy current revision instead of rotating every two hours", () => {
  const workflow = readFileSync(new URL("../.github/workflows/technocore-activity.yml", import.meta.url), "utf8");
  assert.equal(workflow.includes("Do not rotate a healthy current resident"), true);
  assert.equal(workflow.includes('if status_ok "$HEALTH" 0; then'), true);
  assert.equal(workflow.includes("if age < -120 or age > 720"), true);
});

test("watchdog requires exact holder only after takeover and emits bounded diagnostics", () => {
  const workflow = readFileSync(new URL("../.github/workflows/technocore-activity.yml", import.meta.url), "utf8");
  for (const needle of [
    "status.get('protocol') != 'PUI-CLOUD-RESIDENT/2'",
    "status.get('did') != os.environ['EXPECTED_DID']",
    "status.get('revision') != os.environ['EXPECTED_REVISION']",
    "os.environ['REQUIRE_HOLDER'] == '1' and holder != os.environ['HOLDER']",
    'if status_ok "$HEALTH" 1; then',
    "'replyCandidate': status.get('replyCandidate')",
    "'decision': status.get('decision')",
  ]) assert.equal(workflow.includes(needle), true, needle);
});
