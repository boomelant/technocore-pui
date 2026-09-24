"""Fail-closed venue admission and signed-write reconciliation (PUI #20).

This module does not probe production or send by itself. The caller must supply
a contract-bound room capability check and explicit signed envelope, post,
and readback functions. Never retry an outcome-unknown write blindly.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Callable

from .publish_receipt import find_verified_publication
from .signed_envelope import verify_room_envelope

_DEAL_ROOM = re.compile(r"mb-p-tclk-[0-9a-f]{16}")
_NONCE = re.compile(r"[0-9]+")


def assess_new_deal_room(room: str, capability_check: Callable[[str], bool]) -> dict:
    """Admit only after an affirmative fresh check for THIS contract-bound room.

    Discovery and auditing are independent of this result. Callers must not
    substitute writable existing rooms or public /rooms counts for the check.
    A successful check can become stale before the write; write errors remain
    outcome-unknown until exact readback.
    """
    if not isinstance(room, str) or not _DEAL_ROOM.fullmatch(room):
        raise ValueError("expected exact contract-derived mb-p-tclk room")
    try:
        ready = capability_check(room)
    except Exception as exc:
        return {"allowed": False, "classification": "venue_capacity_blocked",
                "room": room, "check_error": type(exc).__name__}
    if ready is not True:
        return {"allowed": False, "classification": "venue_capacity_blocked",
                "room": room}
    return {"allowed": True, "classification": "venue_ready", "room": room}


def publish_if_admitted(
    *,
    admission: dict,
    envelope: dict,
    post: Callable[[str, dict], object],
    readback: Callable[[str], dict],
) -> dict:
    """Exactly one attempt followed by exact independently verified readback.

    Non-publication is NOT established by a missing bounded readback.
    Caller must explicitly handle `venue_write_ambiguous` without retrying.
    The returned record contains public evidence only; no private signing seed.
    """
    if not isinstance(admission, dict) or admission.get("allowed") is not True:
        raise PermissionError("venue admission denied")
    room = admission.get("room")
    if not isinstance(room, str) or not _DEAL_ROOM.fullmatch(room):
        raise ValueError("invalid admitted room")
    if not isinstance(envelope, dict):
        raise ValueError("signed envelope required")
    did, nonce, text, sig = (
        envelope.get("did"), envelope.get("nonce"),
        envelope.get("text"), envelope.get("sig"),
    )
    if not isinstance(nonce, str) or not _NONCE.fullmatch(nonce):
        raise ValueError("nonce must be exact ASCII decimal text")
    if not isinstance(did, str) or not isinstance(text, str) or not isinstance(sig, str):
        raise ValueError("invalid signed envelope shape")
    if not verify_room_envelope(room, {
        "from": did, "nonce": nonce, "text": text, "sig": sig,
    }):
        raise ValueError("invalid signed envelope signature")
    digest = hashlib.sha256(
        f"{room}|{nonce}|{text}|{sig}".encode("utf-8")
    ).hexdigest()
    receipt = {
        "room": room, "did": did, "nonce": nonce,
        "signed_envelope_sha256": digest,
        "source_incidents": ["technocore-chat#688", "technocore-chat#896"],
        "partner_reputation_delta": 0, "settlement_delta": 0,
        "verified_spend_delta": 0, "retry": False,
    }
    try:
        post(room, envelope)
        receipt["http_outcome"] = "returned"
    except Exception as exc:
        # A timeout/503 may happen AFTER the venue accepted the write.
        receipt["http_outcome"] = "exception:" + type(exc).__name__
    try:
        response = readback(room)
        records = response.get("messages", [])
        verified = find_verified_publication(
            room, records, did=did, nonce=nonce, text=text, signature=sig,
        )
    except (LookupError, ValueError, TypeError, KeyError, AttributeError, OSError):
        verified = None
    if verified is None:
        receipt["classification"] = "venue_write_ambiguous"
        receipt["readback"] = "exact_verified_envelope_not_established"
        return receipt
    receipt["classification"] = "published"
    receipt["readback"] = "exact_verified_envelope"
    receipt["seq"] = verified.seq
    return receipt


def append_operational_receipt(path: str | Path, receipt: dict) -> None:
    """Append an operational JSONL receipt locally, with mode 0600.

    The calling agent chooses its durable data directory; no repo auto-push.
    """
    if receipt.get("classification") not in {
        "published", "venue_write_ambiguous", "venue_capacity_blocked"
    }:
        raise ValueError("unexpected operational classification")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(receipt, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(fd, payload)
        os.fsync(fd)
    finally:
        os.close(fd)
