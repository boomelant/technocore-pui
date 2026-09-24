"""Venue gate regression: no blind retries or false settlement evidence."""
import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from pui.venue_gate import (
    append_operational_receipt, assess_new_deal_room, publish_if_admitted,
)

ROOM = "mb-p-tclk-0123456789abcdef"


def envelope(room=ROOM, nonce="9007199254740993111", text="tclk1 valid-fixture"):
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    raw = b"\\xed\\x01" + public
    n = int.from_bytes(raw, "big")
    encoded = ""
    while n:
        n, rem = divmod(n, 58)
        encoded = alphabet[rem] + encoded
    encoded = "1" * (len(raw) - len(raw.lstrip(b"\\0"))) + encoded
    signature = key.sign(f"{room}|{nonce}|{text}".encode())
    return {
        "did": "did:key:z" + encoded, "nonce": nonce, "text": text,
        "sig": base64.urlsafe_b64encode(signature).decode().rstrip("="),
    }


def test_only_exact_derived_room_can_be_checked():
    with pytest.raises(ValueError):
        assess_new_deal_room("technocore", lambda r: True)
    with pytest.raises(ValueError):
        assess_new_deal_room("../mb-p-tclk-0123456789abcdef", lambda r: True)


def test_cap_reached_blocks_write_even_if_existing_rooms_work():
    admission = assess_new_deal_room(ROOM, lambda room: False)
    assert admission["classification"] == "venue_capacity_blocked"
    with pytest.raises(PermissionError):
        publish_if_admitted(
            admission=admission, envelope=envelope(),
            post=lambda *args: pytest.fail("posted despite capacity blocker"),
            readback=lambda room: pytest.fail("read despite admission failure"),
        )


def test_probe_error_fails_closed():
    def offline(room):
        raise TimeoutError("capacity probe timed out")
    decision = assess_new_deal_room(ROOM, offline)
    assert decision["allowed"] is False
    assert decision["check_error"] == "TimeoutError"


def test_successful_fresh_probe_can_reenable_admission():
    assert assess_new_deal_room(ROOM, lambda r: False)["allowed"] is False
    assert assess_new_deal_room(ROOM, lambda r: True)["allowed"] is True


def test_timeout_then_exact_signed_readback_counts_once():
    body = envelope()
    calls = []

    def timed_out(room, signed):
        calls.append((room, signed))
        raise TimeoutError("write accepted but response timed out")

    result = publish_if_admitted(
        admission=assess_new_deal_room(ROOM, lambda r: True),
        envelope=body, post=timed_out,
        readback=lambda room: {
            "messages": [{"from": body["did"], "seq": 42,
                          "nonce": body["nonce"], "text": body["text"],
                          "sig": body["sig"]}],
        },
    )
    assert len(calls) == 1
    assert result["classification"] == "published"
    assert result["seq"] == 42
    assert result["retry"] is False
    assert result["settlement_delta"] == 0


def test_ambiguous_timeout_does_not_retry_or_penalize_partner(tmp_path):
    body = envelope()
    calls = []

    def timed_out(room, signed):
        calls.append(1)
        raise TimeoutError("uncertain")

    result = publish_if_admitted(
        admission=assess_new_deal_room(ROOM, lambda r: True),
        envelope=body, post=timed_out,
        readback=lambda room: {"messages": []},
    )
    assert len(calls) == 1
    assert result["classification"] == "venue_write_ambiguous"
    assert result["retry"] is False
    assert result["partner_reputation_delta"] == 0
    assert result["verified_spend_delta"] == 0
    assert "seq" not in result

    path = tmp_path / "receipts" / "venue.jsonl"
    append_operational_receipt(path, result)
    assert '"venue_write_ambiguous"' in path.read_text()
    assert path.stat().st_mode & 0o077 == 0


def test_wrong_signature_cannot_confirm_publication():
    body = envelope()
    other = envelope(text="other")
    result = publish_if_admitted(
        admission=assess_new_deal_room(ROOM, lambda r: True),
        envelope=body, post=lambda room, signed: None,
        readback=lambda room: {
            "messages": [{
                "from": body["did"], "seq": 43,
                "nonce": body["nonce"], "text": body["text"],
                "sig": other["sig"],
            }],
        },
    )
    assert result["classification"] == "venue_write_ambiguous"


def test_malformed_nonce_rejected_before_post():
    body = envelope()
    body["nonce"] = "9007199254740993111.0"
    with pytest.raises(ValueError, match="nonce"):
        publish_if_admitted(
            admission=assess_new_deal_room(ROOM, lambda r: True),
            envelope=body,
            post=lambda *args: pytest.fail("bad nonce posted"),
            readback=lambda room: pytest.fail("bad nonce read"),
        )
