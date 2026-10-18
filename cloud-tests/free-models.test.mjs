import assert from "node:assert/strict";
import test from "node:test";
import { FREE_MODELS } from "../src/cloud/core.mjs";
import {
  GENERATIVE_FREE_MODELS,
  PUI_RESIDENT_REVISION,
} from "../src/cloud/participation.mjs";

const EXPECTED_FREE_MODELS = [
  "inclusionai/ling-3.0-tiny-free",
  "poolside/laguna-s-2.1-free",
];

test("resident uses only explicitly free current AI Gateway model IDs", () => {
  assert.deepEqual(GENERATIVE_FREE_MODELS, EXPECTED_FREE_MODELS);
  assert.deepEqual(FREE_MODELS, EXPECTED_FREE_MODELS);
  assert.ok(GENERATIVE_FREE_MODELS.every((model) => model.endsWith("-free")));
});

test("resident revision changes when decision model routing changes", () => {
  assert.equal(PUI_RESIDENT_REVISION, "active-replies-v6-free-models");
});
