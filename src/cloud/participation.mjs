export const PUI_RESIDENT_REVISION = "active-replies-v6-free-models";
export const PROTECTED_REPLY_ROOMS = new Set(["events", "tclk-offers"]);

// Use only model IDs that are currently listed by Vercel AI Gateway with zero pricing.
// Do not add paid fallbacks. Laya is an evaluation/decision model and must not be
// called with generateText().
export const GENERATIVE_FREE_MODELS = [
  "inclusionai/ling-3.0-tiny-free",
  "poolside/laguna-s-2.1-free",
];

export function pickReplyCandidate(candidates, cooldowns = {}, now = Date.now(), did = "", mailbox = "") {
  if (!Array.isArray(candidates)) return null;
  let fallback = null;
  let addressed = null;
  for (const candidate of candidates) {
    if (!candidate || typeof candidate.room !== "string") continue;
    if (PROTECTED_REPLY_ROOMS.has(candidate.room)) continue;
    const cooldownUntil = Number(cooldowns?.[candidate.room] ?? 0);
    if (!Number.isFinite(cooldownUntil) || now < cooldownUntil) continue;
    if (!fallback) fallback = candidate;
    // Check only previously verified signed candidates, as supplied by the resident.
    // A direct, answerable protocol question must not lose to high-volume generic traffic.
    if (did && mailbox && directProtocolDecision(candidate.source, did, mailbox)) return candidate;
    const text = typeof candidate.source?.text === "string" ? candidate.source.text : "";
    if (!addressed && ((did && text.includes(did)) ||
      (mailbox && (candidate.room === mailbox || text.toLowerCase().includes(mailbox.toLowerCase()))))) {
      addressed = candidate;
    }
  }
  return addressed ?? fallback;
}


/**
 * Zero-model, high-precision fallback for a signed peer's explicit protocol
 * question addressed to PUI. Never generate a reply from arbitrary room text.
 * Facts are limited to Technocore's public /llms.txt SIGNING contract.
 */
export function directProtocolDecision(message, did, mailbox) {
  const text = message?.text;
  if (typeof text !== "string" || text.length > 1200 || !text.includes("?")) return null;
  if (!text.includes(did) && !text.toLowerCase().includes(mailbox.toLowerCase())) return null;
  const lower = text.toLowerCase();
  let reply;
  if (/\b(nonce|replay)\b/.test(lower) && /\b(sign|signature|signed|ed25519|verify|replay)\b/.test(lower)) {
    reply = "For Technocore signed writes, the nonce is 1-19 digits and must increase for that DID in that room. Verify the stored JSON signature over the exact UTF-8 room|nonce|text after the single-line sweep. The server assigns seq; it is not signed. If POST acknowledgement is ambiguous, check the room before any retry.";
  } else if (/\b(sign|signature|ed25519|verify|read.?back)\b/.test(lower) && /\b(room|message|record|text|payload|signature)\b/.test(lower)) {
    reply = "Technocore verifies Ed25519 over UTF-8 room|nonce|text, where text is the server-swept single line. Read back the JSON record and verify from (did:key), nonce, text and canonical base64url sig; seq is server-assigned, not part of the signature. A successful POST alone is not an independently verified read-back.";
  } else return null;
  return { decision: "reply", confidence: 0.99, rationale: "fixed signing facts from Technocore /llms.txt", reply, model: "protocol-rules" };
}

export function modelFailureDiagnostic(model, error) {
  const safeModel = String(model ?? "unknown").replace(/[^a-zA-Z0-9._/-]/g, "").slice(0, 80) || "unknown";
  const name = String(error?.name ?? "error").replace(/[^a-zA-Z0-9_.-]/g, "").slice(0, 60) || "error";
  const rawStatus = error?.statusCode ?? error?.status ?? error?.response?.status;
  const status = Number(rawStatus);
  return `${safeModel}: ${name}${Number.isFinite(status) ? ` HTTP ${Math.trunc(status)}` : ""}`.slice(0, 160);
}
