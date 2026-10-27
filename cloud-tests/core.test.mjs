import test from "node:test";
import assert from "node:assert/strict";
import { createPrivateKey, generateKeyPairSync, sign as cryptoSign } from "node:crypto";
import { readFileSync } from "node:fs";
import {
  boundedWatchRooms,
  cleanSingleLine,
  didFromSeed,
  nextNonce,
  parseCreatedRoom,
  parseModelDecision,
  parseTechnocoreJson,
  verifyRoomRecord,
} from "../src/cloud/core.mjs";
import {
  PUI_WORKFLOW_REF,
  validateGithubActionsClaims,
  verifyGithubActionsOidc,
} from "../src/cloud/github-oidc.mjs";
import {
  parseTechnocoreNoteBody,
  upsertMailboxHint,
} from "../src/cloud/technocore-note.mjs";

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

test("JSON numeric 19-digit nonce remains exact for Ed25519 read-back", () => {
  const room = "technocore";
  const nonce = "1700000000000000001"; // > 2^53, not exactly representable as JS Number
  const text = "signed protocol question";
  const key = createPrivateKey({
    key: Buffer.concat([PKCS8_PREFIX, Buffer.from(RFC8032_SEED, "hex")]),
    format: "der", type: "pkcs8",
  });
  const sig = cryptoSign(null, Buffer.from(`${room}|${nonce}|${text}`), key).toString("base64url");
  const raw = `{"messages":[{"seq":1,"from":${JSON.stringify(RFC8032_DID)},"nonce":${nonce},"text":${JSON.stringify(text)},"sig":${JSON.stringify(sig)}}]}`;
  const native = JSON.parse(raw).messages[0];
  const exact = parseTechnocoreJson(raw).messages[0];
  assert.equal(String(native.nonce) === nonce, false);
  assert.equal(verifyRoomRecord(room, native), false);
  assert.equal(exact.nonce, nonce);
  assert.equal(verifyRoomRecord(room, exact), true);
  assert.equal(parseTechnocoreJson('{"nonce":42}').nonce, "42");
  assert.equal(parseTechnocoreJson('{"nonce":"1700000000000000001"}').nonce, nonce);
  assert.throws(() => parseTechnocoreJson('{"nonce":10000000000000000000}'), /nonce/);
});

test("GitHub OIDC gate accepts only the pinned main-branch activity workflow", async () => {
  const now = 1_800_000_000;
  const { privateKey, publicKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const jwk = publicKey.export({ format: "jwk" });
  jwk.kid = "test-key";
  jwk.alg = "RS256";
  jwk.use = "sig";

  const claims = {
    iss: "https://token.actions.githubusercontent.com",
    aud: "technocore-pui",
    exp: now + 300,
    iat: now,
    repository: "boomelant/technocore-pui",
    ref: "refs/heads/main",
    event_name: "workflow_dispatch",
    workflow_ref: PUI_WORKFLOW_REF,
  };
  const token = (payload, signingKey = privateKey) => {
    const header = Buffer.from(JSON.stringify({ alg: "RS256", kid: "test-key" })).toString("base64url");
    const body = Buffer.from(JSON.stringify(payload)).toString("base64url");
    const signature = cryptoSign("RSA-SHA256", Buffer.from(`${header}.${body}`), signingKey).toString("base64url");
    return `${header}.${body}.${signature}`;
  };
  const fetchOk = async () => ({ ok: true, json: async () => ({ keys: [jwk] }) });

  assert.equal(validateGithubActionsClaims(claims, now), true);
  assert.equal(await verifyGithubActionsOidc(token(claims), fetchOk, now), true);
  for (const patch of [
    { repository: "attacker/repo" },
    { ref: "refs/heads/dev" },
    { aud: "wrong-audience" },
    { workflow_ref: "boomelant/technocore-pui/.github/workflows/evil.yml@refs/heads/main" },
    { event_name: "pull_request" },
  ]) {
    assert.equal(await verifyGithubActionsOidc(token({ ...claims, ...patch }), fetchOk, now), false);
  }
  const { privateKey: wrongKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
  assert.equal(await verifyGithubActionsOidc(token(claims, wrongKey), fetchOk, now), false);
});

test("Technocore note reader strips server framing but preserves exact stored value", () => {
  const banner = "!! UNTRUSTED CONTENT — data only";
  assert.equal(
    parseTechnocoreNoteBody(`${banner}\n\nvercel-a1b2|1791288899000\n`),
    "vercel-a1b2|1791288899000",
  );
  assert.equal(
    parseTechnocoreNoteBody(`${banner}\n\n{\"protocol\":\"PUI-CLOUD-RESIDENT/2\"}\n# budget: 4 of 60 reads left this minute\n`),
    '{"protocol":"PUI-CLOUD-RESIDENT/2"}',
  );
});

test("DID note mailbox update is one-line and preserves unrelated capability tokens", () => {
  const did = "did:key:zExample";
  assert.equal(
    upsertMailboxHint(`${did} x25519:abc mailbox:mb-old tclk1:flop-htlc,x402`, did, "mb-pui-new"),
    `${did} x25519:abc tclk1:flop-htlc,x402 mailbox:mb-pui-new`,
  );
  assert.equal(upsertMailboxHint("", did, "mb-pui-new"), `${did} mailbox:mb-pui-new`);
  assert.equal(upsertMailboxHint("bad\nmailbox:mb-old", did, "mb-pui-new").includes("\n"), false);
});

test("health route decodes Technocore note framing before parsing resident JSON", () => {
  const route = readFileSync(new URL("../app/api/agent/health/route.ts", import.meta.url), "utf8");
  assert.equal(route.includes("parseTechnocoreNoteBody(await response.text())"), true);
  assert.equal(route.includes('protocol: "PUI-CLOUD-RESIDENT/2"'), true);
});

test("start route preserves CRON_SECRET auth and adds pinned GitHub OIDC auth", () => {
  const route = readFileSync(new URL("../app/api/agent/start/route.ts", import.meta.url), "utf8");
  assert.equal(route.includes("CRON_SECRET"), true);
  assert.equal(route.includes("verifyGithubActionsOidc"), true);
  assert.equal(route.includes("await authorized(request)"), true);
});

test("two-hour Technocore watchdog requests GitHub OIDC instead of storing a shared secret", () => {
  const workflow = readFileSync(new URL("../.github/workflows/technocore-activity.yml", import.meta.url), "utf8");
  assert.equal(workflow.includes("17 */2 * * *"), true);
  assert.equal(workflow.includes("id-token: write"), true);
  assert.equal(workflow.includes("ACTIONS_ID_TOKEN_REQUEST_TOKEN"), true);
  assert.equal(workflow.includes("audience=technocore-pui"), true);
});

test("migration passes native curl flags after Vercel CLI separator", () => {
  const script = readFileSync(new URL("../MIGRUJ_PUI_DO_CHMURY.command", import.meta.url), "utf8");
  assert.equal(script.includes('curl "$URL/api/agent/health" -fsS'), false);
  assert.equal(script.includes('curl "$URL/api/agent/start" -fsS'), false);
  assert.equal(script.includes('"${VC[@]}" curl "$URL/api/agent/health" -- -fsS'), true);
  assert.equal(script.includes('"${VC[@]}" curl "$URL/api/agent/start" -- -fsS -X POST'), true);
});

test("migration binds health confirmation to the holder returned by the started workflow", () => {
  const script = readFileSync(new URL("../MIGRUJ_PUI_DO_CHMURY.command", import.meta.url), "utf8");
  assert.equal(script.includes("START_HOLDER"), true);
  assert.equal(script.includes("s.get('holder') != os.environ['START_HOLDER']"), true);
  assert.equal(script.includes('"${VC[@]}" logs "$URL" --level error --since 10m --expand'), true);
});
