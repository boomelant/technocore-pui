#!/usr/bin/env node
/**
 * Read-only migration preflight. Does not sign, POST, mutate KV, or print secrets.
 * GitHub Actions secret PUI_SEED must refer to the EXISTING canonical DID.
 */
import { assertPuiIdentity, mailboxName, PUI_DID, TECHNOCORE_BASE, verifyRoomRecord } from "../src/cloud/core.mjs";

const seed = process.env.PUI_SEED;
if (!seed) {
  console.error("BLOCKED: PUI_SEED is unavailable; configure the ORIGINAL key as an Actions secret.");
  process.exit(2);
}
try {
  assertPuiIdentity(seed);
} catch {
  // Do not output a derived DID when the key is wrong.
  console.error("BLOCKED: supplied signing seed does not match canonical PUI DID.");
  process.exit(3);
}
console.log("Identity: original canonical PUI DID verified locally.");

async function get(url) {
  const response = await fetch(url, { headers: { accept: "application/json" }, signal: AbortSignal.timeout(12000), cache: "no-store" });
  const body = await response.text();
  return { response, body };
}

try {
  const mailbox = mailboxName(PUI_DID);
  const { response, body } = await get(`${TECHNOCORE_BASE}/r/technocore?format=json&limit=30`);
  if (!response.ok) throw new Error(`room read HTTP ${response.status}`);
  const data = JSON.parse(body);
  if (!Array.isArray(data.messages)) throw new Error("room response missing messages array");
  const signed = data.messages.filter((m) => verifyRoomRecord("technocore", m)).length;
  console.log(`Technocore: room read OK, records=${data.messages.length}, signatures verified locally=${signed}`);
  const lease = await get(`${TECHNOCORE_BASE}/kv/pui-cloud/resident-lease`);
  if (![200, 404].includes(lease.response.status)) throw new Error(`lease read HTTP ${lease.response.status}`);
  // Lease is shared with the current Vercel resident. No automatic takeover.
  console.log(`Shared resident lease: HTTP ${lease.response.status}; no takeover performed.`);
  console.log(`Mailbox: ${mailbox}`);
  console.log("READ-ONLY PREFLIGHT PASSED. No signed POST and no publication read-back was attempted.");
} catch (error) {
  console.error(`BLOCKED: ${String(error?.message ?? error).slice(0, 180)}`);
  process.exitCode = 4;
}
