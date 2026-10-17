import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const workflow = readFileSync(new URL("../workflows/pui-agent.ts", import.meta.url), "utf8");

test("mailbox presence is not counted as a public Technocore reply", () => {
  assert.match(workflow, /totalReplies:\s*0,/);
  assert.doesNotMatch(workflow, /totalReplies:\s*bootstrap\.presence/);
});

test("reply count increments only after confirmed signed post", () => {
  assert.match(workflow, /if \(posted\.status === "confirmed"\) state\.totalReplies \+= 1;/);
});
