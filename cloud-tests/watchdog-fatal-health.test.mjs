import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

// Exercise the Python preflight embedded in the watchdog workflow, not a copy.
const workflow = readFileSync(new URL('../.github/workflows/technocore-activity.yml', import.meta.url), 'utf8');
const match = workflow.match(/          status_ok\(\) \{[\s\S]*?python3 - <<'PY'\n([\s\S]*?)\n          PY/);
assert.ok(match, 'status_ok Python heredoc must remain present');
const script = match[1].split('\n').map(line => line.startsWith('          ') ? line.slice(10) : line).join('\n');
const DID = 'did:key:z6Mkub4QuoxnRWkzjKLmJtcikyoYjVEhrZVtvs2EA3PX1N3f';
const HOLDER = 'gh-39918763554-1';
const REVISION = 'active-replies-v6-free-models';
const base = () => ({
  residentStatus: {
    protocol: 'PUI-CLOUD-RESIDENT/2', revision: REVISION, did: DID,
    holder: HOLDER, at: new Date().toISOString(), cycle: 1234,
    decision: { decision: 'observe', failure: 'poolside/laguna-s-2.1-free: GatewayInternalServerError HTTP 403' },
    totalReplies: 0,
  },
});
function check(value, requireHolder = '0') {
  const run = spawnSync('python3', ['-c', script], {
    env: { ...process.env, HEALTH_JSON: JSON.stringify(value), REQUIRE_HOLDER: requireHolder,
      HOLDER, EXPECTED_REVISION: REVISION, EXPECTED_DID: DID },
    encoding: 'utf8', timeout: 5000,
  });
  assert.equal(run.error, undefined, run.error?.message);
  return run;
}

test('live resident remains healthy despite a free-model HTTP 403', () => {
  const run = check(base());
  assert.equal(run.status, 0, run.stderr);
  assert.equal(JSON.parse(run.stdout).totalReplies, 0);
});

test('terminal observe_failed phase rejects even a fresh status', () => {
  const status = base();
  status.residentStatus.phase = 'observe_failed';
  status.residentStatus.decision.failure = 'runtime observe_failed: FatalError: Step exceeded max retries';
  assert.notEqual(check(status).status, 0);
});

test('terminal phase rejects even when decision is missing', () => {
  const status = base();
  status.residentStatus.phase = 'observe_failed';
  status.residentStatus.decision = null;
  assert.notEqual(check(status).status, 0);
});

test('legacy terminal failure marker rejects without phase', () => {
  const status = base();
  status.residentStatus.decision.failure = 'runtime observe_failed: FatalError';
  assert.notEqual(check(status).status, 0);
});

test('wrong DID, stale status, wrong holder and zero cycle fail closed', () => {
  const wrongDid = base(); wrongDid.residentStatus.did = 'did:key:other';
  assert.notEqual(check(wrongDid).status, 0);
  const stale = base(); stale.residentStatus.at = '2026-01-01T00:00:00Z';
  assert.notEqual(check(stale).status, 0);
  const wrongHolder = base(); wrongHolder.residentStatus.holder = 'gh-other-1';
  assert.notEqual(check(wrongHolder, '1').status, 0);
  const zeroCycle = base(); zeroCycle.residentStatus.cycle = 0;
  assert.notEqual(check(zeroCycle).status, 0);
});
