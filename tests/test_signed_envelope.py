import base64

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from pui.signed_envelope import verify_room_envelope


ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(raw: bytes) -> str:
    zeros = len(raw) - len(raw.lstrip(b"\0"))
    number = int.from_bytes(raw, "big")
    out = ""
    while number:
        number, rem = divmod(number, 58)
        out = ALPHABET[rem] + out
    return "1" * zeros + out


def envelope(room="flop_labs", nonce="1790147478825", text="useful telemetry"):
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    did = "did:key:z" + b58encode(b"\xed\x01" + public)
    payload = f"{room}|{nonce}|{text}".encode()
    sig = base64.urlsafe_b64encode(private.sign(payload)).decode().rstrip("=")
    return room, {"from": did, "nonce": nonce, "text": text, "sig": sig}


def test_valid_envelope_verifies():
    room, record = envelope()
    assert verify_room_envelope(room, record) is True


def test_text_mutation_fails():
    room, record = envelope()
    record["text"] += "!"
    assert verify_room_envelope(room, record) is False


def test_nonce_mutation_fails():
    room, record = envelope()
    record["nonce"] = str(int(record["nonce"]) + 1)
    assert verify_room_envelope(room, record) is False


def test_signature_mutation_fails():
    room, record = envelope()
    raw = bytearray(base64.urlsafe_b64decode(record["sig"] + "=="))
    raw[0] ^= 1
    record["sig"] = base64.urlsafe_b64encode(bytes(raw)).decode().rstrip("=")
    assert verify_room_envelope(room, record) is False


def test_large_nonce_is_preserved_as_text():
    nonce = "999999999999999999999999999999999999999999999999"
    room, record = envelope(nonce=nonce)
    assert verify_room_envelope(room, record) is True


def test_numeric_nonce_fails_closed():
    room, record = envelope()
    record["nonce"] = int(record["nonce"])
    with pytest.raises(ValueError, match="exact decimal text"):
        verify_room_envelope(room, record)
