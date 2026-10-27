import test from "node:test";
import assert from "node:assert/strict";
import {
  GENERATIVE_FREE_MODELS,
  directProtocolDecision,
  modelFailureDiagnostic,
  pickReplyCandidate,
} from "../src/cloud/participation.mjs";

test("protected observation cannot monopolize active reply selection", () => {
  const candidates = [
    { room: "tclk-offers", source: { seq: 10 }, score: 9 },
    { room: "technocore", source: { seq: 11 }, score: 7 },
  ];
  assert.equal(pickReplyCandidate(candidates, {}, 1000), candidates[1]);
});

test("reply selection respects cooldown and keeps searching", () => {
  const candidates = [
    { room: "technocore", source: { seq: 11 }, score: 8 },
    { room: "flop-network", source: { seq: 12 }, score: 7 },
  ];
  assert.equal(pickReplyCandidate(candidates, { technocore: 2000 }, 1000), candidates[1]);
});

test("reply selection fails closed when only protected rooms exist", () => {
  assert.equal(pickReplyCandidate([
    { room: "events", source: { seq: 1 }, score: 10 },
    { room: "tclk-offers", source: { seq: 2 }, score: 9 },
  ], {}, 1000), null);
});

test("generateText fallbacks are explicit non-billing free IDs and exclude Laya", () => {
  assert.deepEqual(GENERATIVE_FREE_MODELS, [
    "inclusionai/ling-3.0-tiny-free",
    "poolside/laguna-s-2.1-free",
  ]);
  assert.equal(GENERATIVE_FREE_MODELS.every((model) => model.endsWith("-free")), true);
  assert.equal(GENERATIVE_FREE_MODELS.some((model) => model.includes("laya")), false);
});

test("model failure diagnostic exposes status without leaking message text", () => {
  const error = Object.assign(new Error("secret bearer token should never appear"), { name: "AI_APICallError", statusCode: 401 });
  assert.equal(modelFailureDiagnostic("inclusionai/ling-3.0-tiny-free", error), "inclusionai/ling-3.0-tiny-free: AI_APICallError HTTP 401");
});

const DID = "did:key:z6Mkub4QuoxnRWkzjKLmJtcikyoYjVEhrZVtvs2EA3PX1N3f";
const MAILBOX = "mb-pui-1c42fed95c";

test("explicit DID-addressed signature question has a useful zero-model answer", () => {
  const decision = directProtocolDecision({ text: `PUI ${DID}: how do I verify a signed room message?` }, DID, MAILBOX);
  assert.equal(decision?.decision, "reply");
  assert.equal(decision?.model, "protocol-rules");
  assert.match(decision?.reply ?? "", /room\|nonce\|text/);
  assert.match(decision?.reply ?? "", /seq is server-assigned/);
});

test("direct nonce question answers the replay/nonce contract without model", () => {
  const decision = directProtocolDecision({ text: `To ${MAILBOX}: how should signed nonce replay be checked?` }, DID, MAILBOX);
  assert.equal(decision?.decision, "reply");
  assert.match(decision?.reply ?? "", /must increase/);
});

test("no deterministic reply for generic chatter, undirected questions or unrelated direct asks", () => {
  assert.equal(directProtocolDecision({ text: "How do I verify a signed room message?" }, DID, MAILBOX), null);
  assert.equal(directProtocolDecision({ text: `Hello ${DID}, how are you?` }, DID, MAILBOX), null);
  assert.equal(directProtocolDecision({ text: `Please verify ${DID} signed message` }, DID, MAILBOX), null);
  assert.equal(directProtocolDecision({ text: `How do I verify a signed room message? ${DID} ${"x".repeat(1200)}` }, DID, MAILBOX), null);
});

test("explicit DID protocol question outranks generic high-score traffic", () => {
  const candidates = [
    { room: "lobby", source: { seq: 100, text: "general signed protocol discussion" }, score: 12 },
    { room: "technocore", source: { seq: 101, text: `PUI ${DID}: how do I verify a signed room message?` }, score: 5 },
  ];
  assert.equal(pickReplyCandidate(candidates, {}, 1000, DID, MAILBOX), candidates[1]);
});

test("cooldown and protected-room gates still precede direct-reply priority", () => {
  const candidates = [
    { room: "tclk-offers", source: { seq: 101, text: `PUI ${DID}: how do I verify a signed room message?` }, score: 15 },
    { room: "technocore", source: { seq: 102, text: `PUI ${DID}: how do I verify a signed room message?` }, score: 5 },
    { room: "lobby", source: { seq: 103, text: "general signed discussion" }, score: 4 },
  ];
  assert.equal(pickReplyCandidate(candidates, { technocore: 2000 }, 1000, DID, MAILBOX), candidates[2]);
});

test("addressed non-protocol question precedes generic traffic but cannot use fixed answer", () => {
  const candidates = [
    { room: "lobby", source: { seq: 100, text: "general signed protocol discussion" }, score: 10 },
    { room: MAILBOX, source: { seq: 101, text: "Could PUI review this?" }, score: 5 },
  ];
  assert.equal(pickReplyCandidate(candidates, {}, 1000, DID, MAILBOX), candidates[1]);
  assert.equal(directProtocolDecision(candidates[1].source, DID, MAILBOX), null);
});
