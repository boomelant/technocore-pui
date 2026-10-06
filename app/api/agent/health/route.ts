import { didFromSeed, mailboxName, PUI_DID, TECHNOCORE_BASE } from "@/src/cloud/core.mjs";
import { parseTechnocoreNoteBody } from "@/src/cloud/technocore-note.mjs";

export async function GET() {
  let identityMatch = false;
  try {
    identityMatch = Boolean(process.env.PUI_SEED) && didFromSeed(process.env.PUI_SEED) === PUI_DID;
  } catch {
    identityMatch = false;
  }

  let residentStatus: unknown = null;
  try {
    const response = await fetch(`${TECHNOCORE_BASE}/kv/pui-cloud/status`, { cache: "no-store" });
    if (response.ok) {
      const value = parseTechnocoreNoteBody(await response.text());
      try { residentStatus = JSON.parse(value); } catch { residentStatus = null; }
    }
  } catch {
    residentStatus = null;
  }

  return Response.json({
    service: "PUI Cloud Resident",
    protocol: "PUI-CLOUD-RESIDENT/2",
    did: PUI_DID,
    identityMatch,
    mailbox: mailboxName(PUI_DID),
    autonomousWrite: process.env.PUI_AUTONOMOUS_WRITE === "1",
    zeroCostMode: process.env.PUI_ZERO_COST === "1",
    residentStatus,
  });
}
