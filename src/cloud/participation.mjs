export const PUI_RESIDENT_REVISION = "active-replies-v3-free-models";
export const PROTECTED_REPLY_ROOMS = new Set(["events", "tclk-offers"]);

// Use only model IDs that are currently listed by Vercel AI Gateway with zero pricing.
// Do not add paid fallbacks. Laya is an evaluation/decision model and must not be
// called with generateText().
export const GENERATIVE_FREE_MODELS = [
  "inclusionai/ling-3.0-tiny-free",
  "poolside/laguna-s-2.1-free",
];

export function pickReplyCandidate(candidates, cooldowns = {}, now = Date.now()) {
  if (!Array.isArray(candidates)) return null;
  for (const candidate of candidates) {
    if (!candidate || typeof candidate.room !== "string") continue;
    if (PROTECTED_REPLY_ROOMS.has(candidate.room)) continue;
    const cooldownUntil = Number(cooldowns?.[candidate.room] ?? 0);
    if (!Number.isFinite(cooldownUntil) || now < cooldownUntil) continue;
    return candidate;
  }
  return null;
}

export function modelFailureDiagnostic(model, error) {
  const safeModel = String(model ?? "unknown").replace(/[^a-zA-Z0-9._/-]/g, "").slice(0, 80) || "unknown";
  const name = String(error?.name ?? "error").replace(/[^a-zA-Z0-9_.-]/g, "").slice(0, 60) || "error";
  const rawStatus = error?.statusCode ?? error?.status ?? error?.response?.status;
  const status = Number(rawStatus);
  return `${safeModel}: ${name}${Number.isFinite(status) ? ` HTTP ${Math.trunc(status)}` : ""}`.slice(0, 160);
}
