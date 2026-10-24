import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const route = readFileSync(new URL("../app/api/agent/start/route.ts", import.meta.url), "utf8");

function fixture({ seed, valid = true, authorized = true, holder = "gh-123-1", oidc = false, startFails = false } = {}) {
  const calls = [];
  const transformed = route.replace(/^import .*;\s*$/gm, "")
    .replaceAll("request: Request", "request")
    .replace("export const GET = launch;", "const GET = launch;")
    .replace("export const POST = launch;", "const POST = launch;");
  const ctx = {
    process: { env: { PUI_SEED: seed, CRON_SECRET: "fixture-secret" } },
    Response: { json: (body, opts = {}) => ({ body, status: opts.status ?? 200, headers: opts.headers ?? {} }) },
    puiAgentWorkflowV6: "workflow-fixture",
    verifyGithubActionsOidc: async () => authorized,
    assertPuiIdentity: (value) => {
      calls.push("identity");
      if (!valid) throw new Error(`sensitive seed: ${value}`);
      return "canonical";
    },
    start: async () => {
      calls.push("start");
      if (startFails) throw new Error("sensitive workflow failure");
      return { runId: "fixture-run" };
    },
    crypto: { randomUUID: () => "12345678-1234-1234-1234-123456789012" },
    console: { error: () => {} },
  };
  vm.runInNewContext(`${transformed}\nthis.GET=GET;this.POST=POST;`, ctx);
  const request = { headers: { get: (key) => key === "authorization"
    ? (oidc ? "Bearer fixture-oidc" : authorized ? "Bearer fixture-secret" : "Bearer wrong")
    : key === "x-pui-holder" ? holder : null } };
  return { post: () => ctx.POST(request), get: () => ctx.GET(request), calls };
}

for (const method of ["post", "get"]) {
  test(`${method.toUpperCase()} refuses mismatched DID before workflow start`, async () => {
    const f = fixture({ seed: "wrong-fixture", valid: false });
    const response = await f[method]();
    assert.equal(response.status, 503);
    assert.equal(response.body.error, "pui_identity_mismatch");
    assert.equal(response.headers["Cache-Control"], "no-store");
    assert.deepEqual(f.calls, ["identity"]);
    assert.ok(!JSON.stringify(response).includes("wrong-fixture"));
  });
}

test("valid canonical identity starts workflow", async () => {
  const f = fixture({ seed: "valid-fixture" });
  assert.equal((await f.post()).status, 200);
  assert.deepEqual(f.calls, ["identity", "start"]);
});

test("missing seed fails before identity verification and start", async () => {
  const f = fixture();
  assert.equal((await f.post()).status, 503);
  assert.deepEqual(f.calls, []);
});

test("unauthorized request fails before identity verification", async () => {
  const f = fixture({ seed: "valid-fixture", authorized: false });
  assert.equal((await f.post()).status, 401);
  assert.deepEqual(f.calls, []);
});

test("invalid holder fails before workflow start", async () => {
  const f = fixture({ seed: "valid-fixture", holder: "BAD" });
  assert.equal((await f.post()).status, 400);
  assert.deepEqual(f.calls, ["identity"]);
});

test("valid OIDC authorization permits canonical identity", async () => {
  const f = fixture({ seed: "valid-fixture", oidc: true });
  assert.equal((await f.post()).status, 200);
  assert.deepEqual(f.calls, ["identity", "start"]);
});

test("workflow failure remains allowlisted and does not leak exception details", async () => {
  const f = fixture({ seed: "valid-fixture", startFails: true });
  const response = await f.post();
  assert.equal(response.status, 503);
  assert.equal(response.body.error, "workflow_start_failed");
  assert.ok(!JSON.stringify(response).includes("sensitive workflow failure"));
});
