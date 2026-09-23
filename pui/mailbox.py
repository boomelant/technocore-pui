from dataclasses import dataclass

from pui.identity import public_did


@dataclass
class MailboxEvaluation:
    category: str
    confidence: float
    source_trust: str
    policy: str
    execute: bool
    reason: str
    priority: int


def valid_nonce_shape(value) -> bool:
    """Preserve large signed nonces; reject floats, bools and malformed text."""
    if type(value) is int:
        return value >= 0
    if isinstance(value, str):
        return bool(value) and value.isascii() and value.isdecimal()
    return False


def has_signed_shape(record: dict) -> bool:
    sender = record.get("from")
    signature = record.get("sig")
    nonce = record.get("nonce")

    return (
        isinstance(sender, str)
        and sender.startswith("did:key:")
        and isinstance(signature, str)
        and bool(signature)
        and valid_nonce_shape(nonce)
    )


def evaluate_mailbox_event(
    record: dict,
    *,
    root_did: str | None = None,
) -> MailboxEvaluation:
    sender = record.get("from")
    text = str(record.get("text") or "").strip()
    root = root_did or public_did()

    if sender == root:
        return MailboxEvaluation(
            category="mailbox",
            confidence=1.0,
            source_trust="self",
            policy="IGNORE",
            execute=False,
            reason="Self-authored mailbox message",
            priority=0,
        )

    if not has_signed_shape(record):
        return MailboxEvaluation(
            category="mailbox",
            confidence=0.0,
            source_trust="unknown",
            policy="IGNORE",
            execute=False,
            reason="Mailbox record has no signed-message fields",
            priority=0,
        )

    if not text:
        return MailboxEvaluation(
            category="mailbox",
            confidence=1.0,
            source_trust="signed-mailbox",
            policy="IGNORE",
            execute=False,
            reason="Empty signed mailbox message",
            priority=0,
        )

    high_signal_terms = (
        "task",
        "request",
        "offer",
        "help",
        "review",
        "verify",
        "audit",
        "work",
        "job",
        "bounty",
        "tclk1 ",
    )

    if any(term in text.lower() for term in high_signal_terms):
        return MailboxEvaluation(
            category="mailbox",
            confidence=1.0,
            source_trust="signed-mailbox",
            policy="REVIEW",
            execute=False,
            reason="Signed mailbox record contains actionable intent",
            priority=90,
        )

    return MailboxEvaluation(
        category="mailbox",
        confidence=1.0,
        source_trust="signed-mailbox",
        policy="REVIEW",
        execute=False,
        reason="External signed mailbox record",
        priority=70,
    )
