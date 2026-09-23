"""Verified publication receipts for Technocore room messages.

This module deliberately separates signing/publishing from verification.  A
receipt is only marked verified after the exact server-returned envelope is
found and its Ed25519 signature validates independently.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .signed_envelope import verify_room_envelope


@dataclass(frozen=True)
class PublicationReceipt:
    room: str
    seq: int
    did: str
    nonce: str
    text: str
    signature: str
    signature_verified: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def find_verified_publication(
    room: str,
    messages: list[dict[str, Any]],
    *,
    did: str,
    nonce: str,
    text: str,
    signature: str,
) -> PublicationReceipt:
    """Return a receipt only for the exact independently verified envelope.

    Matching all signed fields prevents a nearby message from being mistaken
    for the publication.  Verification is fail-closed: malformed or invalid
    candidates are ignored, and absence of a valid exact readback raises.
    """
    for record in messages:
        if (
            record.get("from") != did
            or record.get("nonce") != nonce
            or record.get("text") != text
            or record.get("sig") != signature
        ):
            continue
        try:
            verified = verify_room_envelope(room, record)
        except (TypeError, ValueError):
            continue
        if not verified:
            continue
        seq = record.get("seq")
        if not isinstance(seq, int):
            raise ValueError("verified server envelope is missing integer seq")
        return PublicationReceipt(
            room=room,
            seq=seq,
            did=did,
            nonce=nonce,
            text=text,
            signature=signature,
            signature_verified=True,
        )
    raise LookupError("exact verified publication not found in server readback")
