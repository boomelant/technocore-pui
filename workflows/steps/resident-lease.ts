import { TECHNOCORE_BASE } from "@/src/cloud/core.mjs";
import { parseTechnocoreNoteBody } from "@/src/cloud/technocore-note.mjs";

const LEASE_NS = "pui-cloud";
const LEASE_KEY = "resident-lease";
const LEASE_TTL_MS = 15 * 60 * 1000;

async function readLease(): Promise<{ found: boolean; value: string | null }> {
  const response = await fetch(
    `${TECHNOCORE_BASE}/kv/${encodeURIComponent(LEASE_NS)}/${encodeURIComponent(LEASE_KEY)}`,
    { cache: "no-store" },
  );
  const text = await response.text();
  if (response.status === 404) return { found: false, value: null };
  if (!response.ok) throw new Error(`lease read HTTP ${response.status}: ${text.slice(0, 160)}`);
  return { found: true, value: parseTechnocoreNoteBody(text) };
}

async function writeLease(value: string, condition: { if?: string; if_absent?: boolean }) {
  const response = await fetch(
    `${TECHNOCORE_BASE}/kv/${encodeURIComponent(LEASE_NS)}/${encodeURIComponent(LEASE_KEY)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value, ...condition }),
      cache: "no-store",
    },
  );
  const text = await response.text();
  return { ok: response.ok, status: response.status, text };
}

function decodeLease(value: string | null): { holder: string; expiresAt: number } | null {
  if (!value) return null;
  const match = value.match(/^([a-z0-9][a-z0-9-]{0,38})\|(\d+)$/);
  if (!match) return null;
  return { holder: match[1], expiresAt: Number(match[2]) };
}

function encodeLease(holder: string, expiresAt: number) {
  if (!/^[a-z0-9][a-z0-9-]{0,38}$/.test(holder)) throw new Error("invalid lease holder");
  return `${holder}|${Math.floor(expiresAt)}`;
}

export async function acquireLeaseStep(holder: string, previousValue: string | null) {
  "use step";

  const now = Date.now();
  const mine = encodeLease(holder, now + LEASE_TTL_MS);
  const current = await readLease();

  if (!current.found) {
    const result = await writeLease(mine, { if_absent: true });
    if (result.ok) return { acquired: true, value: mine, reason: "claimed" };
    if (result.status === 409) return { acquired: false, value: null, reason: "claim_race" };
    throw new Error(`lease claim failed ${result.status}: ${result.text.slice(0, 120)}`);
  }

  const parsed = decodeLease(current.value);
  if (!parsed) return { acquired: false, value: null, reason: "malformed_lease_fail_closed" };

  const isMine = parsed.holder === holder;
  const expired = parsed.expiresAt <= now;
  if (!isMine && !expired) return { acquired: false, value: null, reason: `held_by_${parsed.holder}` };
  if (previousValue && isMine && previousValue !== current.value) {
    return { acquired: false, value: null, reason: "lease_value_changed_fail_closed" };
  }

  const result = await writeLease(mine, { if: current.value ?? "" });
  if (result.ok) return { acquired: true, value: mine, reason: isMine ? "renewed" : "expired_takeover" };
  if (result.status === 409) return { acquired: false, value: null, reason: "cas_lost" };
  throw new Error(`lease renewal failed ${result.status}: ${result.text.slice(0, 120)}`);
}
acquireLeaseStep.maxRetries = 0;
