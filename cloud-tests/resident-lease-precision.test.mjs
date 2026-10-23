import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';

const source = readFileSync(new URL('../workflows/steps/resident-lease.ts', import.meta.url), 'utf8');
const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText;
const now = 1792710000000;

function harness(getStatus, body, postStatus = 200) {
  const calls = [];
  const exports = {};
  const reply = (status, text) => ({ ok: status >= 200 && status < 300, status, text: async () => text });
  vm.runInNewContext(js, {
    exports,
    require(id) {
      if (id.endsWith('/core.mjs')) return { TECHNOCORE_BASE: 'https://technocore.test' };
      if (id.endsWith('/technocore-note.mjs')) return { parseTechnocoreNoteBody: text => text };
      throw new Error(`Unexpected import: ${id}`);
    },
    async fetch(url, init = {}) {
      calls.push({ url, init });
      return init.method === 'POST' ? reply(postStatus, 'write') : reply(getStatus, body);
    },
    Date: class extends Date { static now() { return now; } },
    Number, JSON, Error, String, encodeURIComponent,
  });
  return { run: exports.acquireLeaseStep, posts: () => calls.filter(call => call.init.method === 'POST') };
}

test('unsafe and zero expiry fail closed without CAS write', async () => {
  for (const expiry of ['9007199254740993', '9999999999999999999999', '0']) {
    const h = harness(200, `other|${expiry}`);
    const result = await h.run('current', null);
    assert.equal(result.reason, 'malformed_lease_fail_closed');
    assert.equal(h.posts().length, 0);
  }
});

test('expired lease takeover uses exact prior value as CAS condition', async () => {
  const old = `other|${now - 1}`;
  const h = harness(200, old);
  const result = await h.run('current', null);
  assert.equal(result.reason, 'expired_takeover');
  assert.equal(JSON.parse(h.posts()[0].init.body).if, old);
});

test('unexpired foreign lease and CAS collision never acquire', async () => {
  const active = harness(200, `other|${now + 60000}`);
  assert.equal((await active.run('current', null)).acquired, false);
  assert.equal(active.posts().length, 0);
  const race = harness(200, `other|${now - 1}`, 409);
  assert.equal((await race.run('current', null)).reason, 'cas_lost');
});

test('HTTP 500 on read and claim is never interpreted as success', async () => {
  const read = harness(500, 'unavailable');
  await assert.rejects(read.run('current', null), /lease read HTTP 500/);
  assert.equal(read.posts().length, 0);
  const claim = harness(404, 'missing', 500);
  await assert.rejects(claim.run('current', null), /lease claim failed 500/);
  assert.equal(claim.posts().length, 1);
});
