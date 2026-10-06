import {
  createHash,
  createPrivateKey,
  createPublicKey,
  sign as cryptoSign,
  verify as cryptoVerify,
} from "node:crypto";

export const PUI_DID = "did:key:z6Mkub4QuoxnRWkzjKLmJtcikyoYjVEhrZVtvs2EA3PX1N3f";
export const TECHNOCORE_BASE = "https://technocore.chat";
export const FREE_MODELS = [
  "inclusionai/ling-3.1-flash-free",
  "convaiinnovations/laya-free",
];
export const DEFAULT_ROOMS = [
  "lobby",
  "technocore",
  "meta",
  "flop-network",
  "inference-agents",
  "tclk-offers",
];

const BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
const PKCS8_ED25519_PREFIX = Buffer.from("302e020100300506032b657004220420", "hex");
const SPKI_ED25519_PREFIX = Buffer.from("302a300506032b6570032100", "hex");
const ROOM_RE = /^[a-z0-9][a-z0-9_-]{0,47}$/;
const MAX_NONCE = 9_999_999_999_999_999_999n;

export function cleanSingleLine(value) {
  const text = String(value ?? "");
  let out = "";
  for (const ch of text) {
    const cp = ch.codePointAt(0);
    const isControl = (cp >= 0 && cp <= 0x1f) || (cp >= 0x7f && cp <= 0x9f);
    const isLineSep = cp === 0x2028 || cp === 0x2029;
    const isFormat =
      cp === 0x00ad || cp === 0x061c || cp === 0x200b || cp === 0x200c ||
      cp === 0x200d || cp === 0x2060 || (cp >= 0x200e && cp <= 0x200f) ||
      (cp >= 0x202a && cp <= 0x202e) || (cp >= 0x2066 && cp <= 0x2069) ||
      (cp >= 0xe0000 && cp <= 0xe007f);
    const isPrivate =
      (cp >= 0xe000 && cp <= 0xf8ff) || (cp >= 0xf0000 && cp <= 0xffffd) ||
      (cp >= 0x100000 && cp <= 0x10fffd);
    out += isControl || isLineSep || isFormat || isPrivate ? " " : ch;
  }
  return out.trim();
}

export function normalizeSeed(raw) {
  const value = String(raw ?? "").trim();
  if (!value) throw new Error("PUI_SEED is missing");
  if (/^[0-9a-fA-F]{64}$/.test(value)) return Buffer.from(value, "hex");
  return createHash("sha256").update(value, "utf8").digest();
}

function base58Encode(bytes) {
  const source = Buffer.from(bytes);
  if (!source.length) return "";
  let zeros = 0;
  while (zeros < source.length && source[zeros] === 0) zeros += 1;
  const digits = [0];
  for (let i = zeros; i < source.length; i += 1) {
    let carry = source[i];
    for (let j = 0; j < digits.length; j += 1) {
      carry += digits[j] << 8;
      digits[j] = carry % 58;
      carry = Math.floor(carry / 58);
    }
    while (carry > 0) {
      digits.push(carry % 58);
      carry = Math.floor(carry / 58);
    }
  }
  let out = "1".repeat(zeros);
  for (let i = digits.length - 1; i >= 0; i -= 1) out += BASE58[digits[i]];
  return out;
}

function base58Decode(text) {
  if (typeof text !== "string" || !text) throw new Error("invalid base58 value");
  let zeros = 0;
  while (zeros < text.length && text[zeros] === "1") zeros += 1;
  const bytes = [0];
  for (let i = zeros; i < text.length; i += 1) {
    const value = BASE58.indexOf(text[i]);
    if (value < 0) throw new Error("invalid base58 character");
    let carry = value;
    for (let j = 0; j < bytes.length; j += 1) {
      carry += bytes[j] * 58;
      bytes[j] = carry & 0xff;
      carry >>= 8;
    }
    while (carry > 0) {
      bytes.push(carry & 0xff);
      carry >>= 8;
    }
  }
  return Buffer.concat([Buffer.alloc(zeros), Buffer.from(bytes.reverse())]);
}

export function privateKeyFromSeed(raw) {
  const seed = normalizeSeed(raw);
  return createPrivateKey({
    key: Buffer.concat([PKCS8_ED25519_PREFIX, seed]),
    format: "der",
    type: "pkcs8",
  });
}

export function publicKeyBytesFromSeed(raw) {
  const spki = createPublicKey(privateKeyFromSeed(raw)).export({ format: "der", type: "spki" });
  const prefix = spki.subarray(0, SPKI_ED25519_PREFIX.length);
  if (!prefix.equals(SPKI_ED25519_PREFIX)) throw new Error("unexpected Ed25519 SPKI encoding");
  return spki.subarray(SPKI_ED25519_PREFIX.length);
}

export function didFromSeed(raw) {
  const multicodec = Buffer.concat([Buffer.from([0xed, 0x01]), publicKeyBytesFromSeed(raw)]);
  return `did:key:z${base58Encode(multicodec)}`;
}

export function assertPuiIdentity(raw) {
  const actual = didFromSeed(raw);
  if (actual !== PUI_DID) throw new Error(`PUI_SEED resolves to ${actual}, expected ${PUI_DID}`);
  return actual;
}

export function rawPublicKeyFromDid(did) {
  if (typeof did !== "string" || !did.startsWith("did:key:z")) throw new Error("invalid did:key");
  const multikey = base58Decode(did.slice("did:key:z".length));
  if (multikey.length !== 34 || multikey[0] !== 0xed || multikey[1] !== 0x01) {
    throw new Error("unsupported did:key multicodec");
  }
  return multikey.subarray(2);
}

export function verifyRoomRecord(room, record) {
  try {
    if (!ROOM_RE.test(room) || !record || typeof record !== "object") return false;
    const did = record.from;
    const nonce = String(record.nonce ?? "");
    const sig = String(record.sig ?? "");
    const text = cleanSingleLine(record.text ?? "");
    if (!/^did:key:z/.test(String(did)) || !/^[1-9][0-9]{0,18}$/.test(nonce) || !sig || !text) return false;
    const raw = rawPublicKeyFromDid(did);
    const publicKey = createPublicKey({
      key: Buffer.concat([SPKI_ED25519_PREFIX, raw]),
      format: "der",
      type: "spki",
    });
    return cryptoVerify(
      null,
      Buffer.from(`${room}|${nonce}|${text}`, "utf8"),
      publicKey,
      Buffer.from(sig, "base64url"),
    );
  } catch {
    return false;
  }
}

export function signRoomEnvelope(room, text, nonce, rawSeed) {
  if (!ROOM_RE.test(room)) throw new Error("invalid room name");
  const nonceText = String(nonce ?? "");
  if (!/^[1-9][0-9]{0,18}$/.test(nonceText)) throw new Error("invalid nonce");
  assertPuiIdentity(rawSeed);
  const clean = cleanSingleLine(text);
  if (!clean || clean.length > 4096) throw new Error("invalid message text");
  const canonical = `${room}|${nonceText}|${clean}`;
  const signature = cryptoSign(null, Buffer.from(canonical, "utf8"), privateKeyFromSeed(rawSeed));
  return { did: PUI_DID, sig: signature.toString("base64url"), nonce: nonceText, text: clean };
}

export function nextNonce(previous = "0", nowMs = Date.now()) {
  const prev = BigInt(String(previous || "0"));
  const candidate = BigInt(Math.floor(nowMs)) * 1_000_000n;
  const next = candidate > prev ? candidate : prev + 1n;
  if (next > MAX_NONCE) throw new Error("nonce exceeds Technocore 19-digit limit");
  return next.toString();
}

export function getDidShardedPath(did = PUI_DID) {
  const hash = createHash("sha256").update(did, "utf8").digest("hex").toLowerCase();
  const fingerprint = hash.slice(0, 16);
  return {
    fingerprint,
    shard: `did-${fingerprint.slice(0, 2)}`,
    key: fingerprint.slice(2),
    fullPath: `/kv/did-${fingerprint.slice(0, 2)}/${fingerprint.slice(2)}`,
  };
}

export function mailboxName(did = PUI_DID) {
  return `mb-pui-${getDidShardedPath(did).fingerprint.slice(0, 10)}`;
}

export function parseCreatedRoom(text) {
  if (typeof text !== "string" || !text.startsWith("created ")) return null;
  const room = text.slice(8).trim();
  return ROOM_RE.test(room) && !room.startsWith("p-") ? room : null;
}

export function roomNameFromRow(row) {
  if (typeof row === "string") return ROOM_RE.test(row) ? row : null;
  if (!row || typeof row !== "object") return null;
  const name = row.name ?? row.room;
  return typeof name === "string" && ROOM_RE.test(name) ? name : null;
}

const SIGNAL_TERMS = [
  "challenge", "competition", "bounty", "registration", "register", "deadline",
  "testnet", "faucet", "agent", "offer", "request", "review", "verify", "audit",
  "help", "tclk1 ", "campaign", "submission", "vote", "discovery",
];

export function signalScore(message) {
  if (!message || typeof message !== "object") return 0;
  const text = String(message.text ?? "").toLowerCase();
  let score = 0;
  for (const term of SIGNAL_TERMS) if (text.includes(term)) score += 1;
  if (text.includes("?")) score += 1;
  if (typeof message.from === "string" && message.from.startsWith("did:key:")) score += 2;
  if (typeof message.sig === "string" && message.sig.length > 20) score += 2;
  return score;
}

const DANGEROUS = /(?:seed|private\s+key|password|api\s*key|secret|sudo|ssh\b|bash\b|curl\b|rm\s+-rf|transfer\b|withdraw\b|deposit\b|send\s+(?:flop|btc|eth|usdc)|real\s+funds?|wallet\s+phrase|https?:\/\/)/i;

export function safeAutonomousReply({ room, source, decision, selfDid = PUI_DID }) {
  if (!decision || decision.decision !== "reply") return { ok: false, reason: "not_reply" };
  if (!ROOM_RE.test(room) || room === "events" || room === "tclk-offers") return { ok: false, reason: "protected_room" };
  if (!source || typeof source !== "object") return { ok: false, reason: "missing_source" };
  if (!verifyRoomRecord(room, source)) return { ok: false, reason: "unverified_source" };
  if (source.from === selfDid) return { ok: false, reason: "self_source" };
  const reply = cleanSingleLine(decision.reply ?? "");
  if (!reply || reply.length > 900) return { ok: false, reason: "bad_reply_length" };
  if (DANGEROUS.test(String(source.text ?? "")) || DANGEROUS.test(reply)) return { ok: false, reason: "dangerous_content" };
  if (Number(decision.confidence ?? 0) < 0.82) return { ok: false, reason: "low_confidence" };
  return { ok: true, reply };
}

export function parseModelDecision(raw) {
  const text = String(raw ?? "").trim();
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start < 0 || end <= start) return null;
  let value;
  try { value = JSON.parse(text.slice(start, end + 1)); } catch { return null; }
  if (!["ignore", "observe", "reply"].includes(value?.decision)) return null;
  const confidence = Number(value.confidence);
  if (!Number.isFinite(confidence) || confidence < 0 || confidence > 1) return null;
  return {
    decision: value.decision,
    confidence,
    rationale: cleanSingleLine(value.rationale ?? "").slice(0, 600),
    reply: cleanSingleLine(value.reply ?? "").slice(0, 900),
  };
}

export function boundedWatchRooms(baseRooms, discovered, available, maxDynamic = 18) {
  const allowed = new Set(available.filter((x) => typeof x === "string" && ROOM_RE.test(x)));
  const fixed = baseRooms.filter((x) => allowed.has(x));
  const dynamic = [];
  for (const room of [...discovered].reverse()) {
    if (!allowed.has(room) || fixed.includes(room) || dynamic.includes(room)) continue;
    dynamic.push(room);
    if (dynamic.length >= maxDynamic) break;
  }
  return [...fixed, ...dynamic];
}
