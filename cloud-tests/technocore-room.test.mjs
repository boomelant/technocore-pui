import test from 'node:test';
import assert from 'node:assert/strict';
import { parseTechnocoreRoomJson } from '../src/cloud/technocore-room.mjs';

test('preserves signed 19-digit nonce without IEEE-754 rounding', () => {
  const nonce = '1791872507131605594';
  assert.notEqual(String(Number(nonce)), nonce);
  const result = parseTechnocoreRoomJson(`{"messages":[{"seq":118601387,"nonce":${nonce},"text":"ok"}]}`);
  assert.equal(result.messages[0].nonce, nonce);
  assert.equal(result.messages[0].seq, 118601387);
});

test('accepts future string nonce and leaves escaped message text intact', () => {
  const text = 'literal "nonce":1791872507131605594';
  const result = parseTechnocoreRoomJson(JSON.stringify({ messages: [{ seq: 1, nonce: '1791872507131605594', text }] }));
  assert.equal(result.messages[0].nonce, '1791872507131605594');
  assert.equal(result.messages[0].text, text);
});

test('rejects malformed room response instead of silently observing zero messages', () => {
  assert.throws(() => parseTechnocoreRoomJson('{"messages":null}'), /invalid Technocore/);
  assert.throws(() => parseTechnocoreRoomJson('{'), SyntaxError);
});
