import { createPublicKey, verify as cryptoVerify } from "node:crypto";

export const GITHUB_OIDC_ISSUER = "https://token.actions.githubusercontent.com";
export const GITHUB_OIDC_JWKS = "https://token.actions.githubusercontent.com/.well-known/jwks";
export const PUI_OIDC_AUDIENCE = "technocore-pui";
export const PUI_REPOSITORY = "boomelant/technocore-pui";
export const PUI_WORKFLOW_REF = `${PUI_REPOSITORY}/.github/workflows/technocore-activity.yml@refs/heads/main`;

function decodeJsonPart(part) {
  try {
    return JSON.parse(Buffer.from(part, "base64url").toString("utf8"));
  } catch {
    throw new Error("invalid JWT encoding");
  }
}

function audienceIncludes(aud, expected) {
  return typeof aud === "string" ? aud === expected : Array.isArray(aud) && aud.includes(expected);
}

export function validateGithubActionsClaims(claims, now = Math.floor(Date.now() / 1000)) {
  if (!claims || typeof claims !== "object") return false;
  if (claims.iss !== GITHUB_OIDC_ISSUER || !audienceIncludes(claims.aud, PUI_OIDC_AUDIENCE)) return false;
  if (!Number.isFinite(Number(claims.exp)) || Number(claims.exp) <= now || Number(claims.exp) > now + 900) return false;
  if (claims.nbf != null && Number(claims.nbf) > now + 60) return false;
  if (claims.iat != null && (!Number.isFinite(Number(claims.iat)) || Number(claims.iat) > now + 60 || Number(claims.iat) < now - 900)) return false;
  if (claims.repository !== PUI_REPOSITORY || claims.ref !== "refs/heads/main") return false;
  if (!new Set(["schedule", "workflow_dispatch", "push"]).has(claims.event_name)) return false;
  if (claims.workflow_ref !== PUI_WORKFLOW_REF) return false;
  return true;
}

export async function verifyGithubActionsOidc(token, fetchImpl = fetch, now = Math.floor(Date.now() / 1000)) {
  if (typeof token !== "string" || token.length > 12000) return false;
  const parts = token.split(".");
  if (parts.length !== 3 || parts.some((part) => !part)) return false;

  let header;
  let claims;
  try {
    header = decodeJsonPart(parts[0]);
    claims = decodeJsonPart(parts[1]);
  } catch {
    return false;
  }

  if (header?.alg !== "RS256" || typeof header?.kid !== "string" || !header.kid) return false;
  if (!validateGithubActionsClaims(claims, now)) return false;

  let jwks;
  try {
    const response = await fetchImpl(GITHUB_OIDC_JWKS, { cache: "no-store" });
    if (!response?.ok) return false;
    jwks = await response.json();
  } catch {
    return false;
  }

  const jwk = Array.isArray(jwks?.keys)
    ? jwks.keys.find((key) => key?.kid === header.kid && key?.kty === "RSA" && (!key.alg || key.alg === "RS256"))
    : null;
  if (!jwk) return false;

  try {
    const key = createPublicKey({ key: jwk, format: "jwk" });
    return cryptoVerify(
      "RSA-SHA256",
      Buffer.from(`${parts[0]}.${parts[1]}`, "utf8"),
      key,
      Buffer.from(parts[2], "base64url"),
    );
  } catch {
    return false;
  }
}
