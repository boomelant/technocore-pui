// Technocore documents signed nonces as up to 19 decimal digits. Its JSON
// read lane may emit them as unquoted integers; JSON.parse rounds those above
// 2^53. Quote ONLY the nonce numeric tokens before parsing, preserving the
// exact canonical digits used for Ed25519 verification.
export function parseTechnocoreRoomJson(raw) {
  if (typeof raw !== 'string') throw new TypeError('room JSON must be text');
  const exact = raw.replace(/("nonce"\s*:\s*)([0-9]{1,19})(?=\s*[,}])/g, '$1"$2"');
  const value = JSON.parse(exact);
  if (!value || typeof value !== 'object' || !Array.isArray(value.messages)) {
    throw new Error('invalid Technocore room JSON');
  }
  return value;
}
