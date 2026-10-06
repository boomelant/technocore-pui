export function parseTechnocoreNoteBody(body) {
  const raw = String(body ?? "");
  const start = raw.indexOf("\n\n");
  let value = start === -1 ? raw : raw.slice(start + 2);
  const footer = value.lastIndexOf("\n# budget: ");
  if (footer !== -1) value = value.slice(0, footer);
  return value.replace(/\s+$/, "");
}

export function upsertMailboxHint(value, did, mailbox) {
  const tokens = String(value ?? "")
    .replace(/[\r\n\u2028\u2029]+/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  const kept = tokens.filter((token) => !token.toLowerCase().startsWith("mailbox:"));
  if (!kept.includes(did)) kept.unshift(did);
  kept.push(`mailbox:${mailbox}`);
  return kept.join(" ");
}
