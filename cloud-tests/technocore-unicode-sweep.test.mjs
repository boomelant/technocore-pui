import test from "node:test";
import assert from "node:assert/strict";
import { cleanSingleLine } from "../src/cloud/core.mjs";

test("Technocore Unicode category sweep replaces each forbidden category before trim", () => {
  const input = " \u0000A\u200bB\ue000C\u2028D\u2029E\ud800F\u0085G ";
  assert.equal(cleanSingleLine(input), "A B C D E F G");
});

test("Technocore sweep covers supplementary-plane format and private-use characters", () => {
  assert.equal(cleanSingleLine("a\u{e0001}b\u{f0000}c"), "a b c");
});

test("Technocore does not normalize Unicode or collapse ordinary whitespace", () => {
  assert.equal(cleanSingleLine("e\u0301  \u00e9"), "e\u0301  \u00e9");
});

test("Technocore sweep is idempotent and preserves regular text", () => {
  const value = " TCLK | nonce | hello ";
  assert.equal(cleanSingleLine(cleanSingleLine(value)), cleanSingleLine(value));
  assert.equal(cleanSingleLine(value), "TCLK | nonce | hello");
});
