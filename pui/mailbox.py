from dataclasses import dataclass

from pui.identity import public_did


@dataclass
class MailboxDecision:
    action: str
    reason: str
    priority: int
    signed: bool
    self_message: bool


def is_signed_record(record: dict) -> bool:
    sender = record.get("from")
    signature = record.get("sig")
    nonce = record.get("nonce")

    return (
        isinstance(sender, str)
        and sender.startswith("did:key:")
        and isinstance(signature, str)
        and bool(signature)
        and nonce is not None
    )


def classify_mailbox_record(record: dict) -> MailboxDecision:
    sender = record.get("from")
    text = str(record.get("text") or "").strip()

    signed = is_signed_record(record)
    self_message = sender == public_did()

    if self_message:
        return MailboxDecision(
            action="IGNORE",
            reason="Self-authored mailbox message",
            priority=0,
            signed=signed,
            self_message=True,
        )

    if not signed:
        return MailboxDecision(
            action="IGNORE",
            reason="Unsigned mailbox message",
            priority=0,
            signed=False,
            self_message=False,
        )

    if not text:
        return MailboxDecision(
            action="IGNORE",
            reason="Empty mailbox message",
            priority=0,
            signed=True,
            self_message=False,
        )

    lowered = text.lower()

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

    if any(term in lowered for term in high_signal_terms):
        return MailboxDecision(
            action="REVIEW",
            reason="Signed mailbox message contains actionable intent",
            priority=90,
            signed=True,
            self_message=False,
        )

    return MailboxDecision(
        action="REVIEW",
        reason="Signed mailbox message from external DID",
        priority=70,
        signed=True,
        self_message=False,
    )
