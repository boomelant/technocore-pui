import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const cycle = readFileSync(new URL("../workflows/steps/pui-cycle-v2.ts", import.meta.url), "utf8");

test("resident never emits recurring presence or protocol-test posts", () => {
  assert.doesNotMatch(cycle, /sendSignedTestOnce|SIGNED_TECHNOCORE_TEST|ensurePresence|postSigned/);
  assert.match(cycle, /readMailboxNonce\(mailbox, previousNonce\)/);
  assert.match(cycle, /presence: "read_only"/);
});
test("normal reply verifies source signature and signed room read-back", () => {
  for (const phrase of [
    "verifyRoomRecord(action.room, source)",
    "signRoomEnvelope(action.room, action.reply, action.nonce, seed)",
    "String(m.nonce) === action.nonce",
    "m.sig === envelope.sig",
    "verifyRoomRecord(action.room, m)",
    'status: "unconfirmed"',
  ]) assert.ok(cycle.includes(phrase), phrase);
});
