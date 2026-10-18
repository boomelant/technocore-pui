import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const cycle = readFileSync(new URL("../workflows/steps/pui-cycle-v2.ts", import.meta.url), "utf8");

test("one-shot technical note requires autonomous-write authorization and initial cycle", () => {
  assert.match(cycle, /state\.cycle === 0 && process\.env\.PUI_AUTONOMOUS_WRITE === "1"/);
  assert.match(cycle, /signed-test-20261018/);
  assert.match(cycle, /if_absent: true/);
});
test("signed one-shot verifies precise nonce, signature and sequence on read-back", () => {
  for (const phrase of [
    "signRoomEnvelope(room, text, nonce, seed)",
    "String(m.nonce) === nonce",
    "m.sig === sent.payload.sig",
    "verifyRoomRecord(room, m)",
    "unconfirmed_no_retry",
    "transport_error_no_retry",
  ]) assert.ok(cycle.includes(phrase), phrase);
});
