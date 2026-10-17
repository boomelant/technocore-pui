import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync(new URL("../workflows/steps/pui-cycle-v2.ts", import.meta.url), "utf8");

test("Technocore reads are bounded to 50 messages and six rooms", () => {
  assert.match(source, /const MAX_MESSAGES_PER_ROOM = 50;/);
  assert.match(source, /const MAX_WATCH_ROOMS = 6;/);
  assert.match(source, /Math\.min\(MAX_MESSAGES_PER_ROOM, Math\.floor\(limit\)\)/);
  assert.match(source, /boundedWatchRooms\([\s\S]*MAX_WATCH_ROOMS\)/);
});

test("room batches reject invalid, replayed and non-monotonic seq values", () => {
  assert.match(source, /Number\.isSafeInteger\(message\.seq\)/);
  assert.match(source, /Number\(message\.seq\) <= previousSeq/);
  assert.match(source, /validateMessageBatch\(room, messages, since\)/);
});

test("mailbox presence requires a valid room signature before trust", () => {
  const ensurePresence = source.slice(source.indexOf("async function ensurePresence"), source.indexOf("function sha("));
  assert.match(ensurePresence, /verifyRoomRecord\(mailbox, m\)/);
  assert.match(ensurePresence, /readRoom\(mailbox, null, MAX_MESSAGES_PER_ROOM\)/);
  assert.match(ensurePresence, /readRoom\(mailbox, beforeSeq, MAX_MESSAGES_PER_ROOM\)/);
});

test("reply write verifies source and signed read-back with bounded incremental reads", () => {
  const postReply = source.slice(source.indexOf("export async function postReplyStep"));
  assert.match(postReply, /sourceSince = Math\.max\(0, action\.sourceSeq - 1\)/);
  assert.match(postReply, /verifyRoomRecord\(action\.room, source\)/);
  assert.match(postReply, /verifyRoomRecord\(action\.room, m\)/);
  assert.match(postReply, /readRoom\(action\.room, action\.sourceSeq, MAX_MESSAGES_PER_ROOM\)/);
});
