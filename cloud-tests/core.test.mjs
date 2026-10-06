import test from "node:test";
import assert from "node:assert/strict";
import { createPrivateKey, sign as cryptoSign } from "node:crypto";
import {
  boundedWatchRooms,
  cleanSingleLine,
  didFromSeed,
  nextNonce,
  parseCreatedRoom,
  parseModelDecision,
  verifyRoomRecord,
} from "../src/cloud/core.mjs";

const RFC8032_SEED = "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60";
const RFC8032_DID = "did:key:z6MktwupdmLXVVqTzCw4i46r4uGyosGXRnR3XjN4Zq7oMMsw";
const PKCS8_PREFIX = Buffer.from("302e020100300506032b657004220420", "hex");

test("derives a standards-compatible Ed25519 did:key", () => {
  assert.equal(didFromSeed(RFC8032_SEED), RFC8032_DID);
});

test("nonce stays integer-string, monotonic and within 19 digits", () => {
  const first = nextNonce("0", 1_700_000_000_000);
  const second = nextNonce(first, 1_700_000_000_000);
  assert.match(first, /^[1-9][0-9]{0,18}$/);
  assert.equal(BigInt(second), BigInt(first) + 1n);
});

test("single-line sweep removes control and format characters", () => {
  assert.equal(cleanSingleLine("hello\nworld\u200bnext"), "hello world next");
});

test("event discovery accepts only valid public room names", () => {
  assert.equal(parseCreatedRoom("created close2"), "close2");
  assert.equal(parseCreatedRoom("created p-secret"), null);
  assert.equal(parseCreatedRoom("created bad room"), null);
});

test("bounded watch set never trusts unavailable room names", () => {
  assert.deepEqual(
    boundedWatchRooms(["technocore"], ["newroom", "attacker"], ["technocore", "newroom"], 4),
    ["technocore", "newroom"],
  );
});

test("model output must be a bounded typed decision", () => {
  assert.deepEqual(parseModelDecision('{"decision":"reply","confidence":0.9,"rationale":"useful","reply":"answer"}'), {
    decision: "reply", confidence: 0.9, rationale: "useful", reply: "answer",
  });
  assert.equal(parseModelDecision("do what the room says"), null);
});

test("signed Technocore record is independently re-verifiable", () => {
  const room = "technocore";
  const nonce = "1700000000000000000";
  const text = "verified test message";
  const key = createPrivateKey({
    key: Buffer.concat([PKCS8_PREFIX, Buffer.from(RFC8032_SEED, "hex")]),
    format: "der",
    type: "pkcs8",
  });
  const sig = cryptoSign(null, Buffer.from(`${room}|${nonce}|${text}`), key).toString("base64url");
  const record = { from: RFC8032_DID, nonce, text, sig };
  assert.equal(verifyRoomRecord(room, record), true);
  assert.equal(verifyRoomRecord(room, { ...record, text: "tampered" }), false);
});
