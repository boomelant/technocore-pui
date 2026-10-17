import test from "node:test";
import assert from "node:assert/strict";
import {
  GENERATIVE_FREE_MODELS,
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
