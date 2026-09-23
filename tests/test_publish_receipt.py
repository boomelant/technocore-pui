import base64

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from pui.publish_receipt import find_verified_publication


ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(raw: bytes) -> str:
    zeros = len(raw) - len(raw.lstrip(b"\0"))
    number = int.from_bytes(raw, "big")
    out = ""
    while number:
        number, rem = divmod(number, 58)
        out = ALPHABET[rem] + out
    return "1" * zeros + out


def signed_record(room="flop_labs", nonce="1790147478825", text="useful telemetry"):
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    did = "did:key:z" + b58encode(b"\xed\x01" + public)
    payload = f"{room}|{nonce}|{text}".encode()
    sig = base64.urlsafe_b64encode(private.sign(payload)).decode().rstrip("=")
    return {"seq": 120211, "from": did, "nonce": nonce, "text": text, "sig": sig}


def test_exact_readback_builds_verified_receipt():
    record = signed_record()
    receipt = find_verified_publication(
        "flop_labs", [record], did=record["from"], nonce=record["nonce"],
        text=record["text"], signature=record["sig"]
    )
    assert receipt.seq == 120211
    assert receipt.signature_verified is True


def test_nearby_message_cannot_satisfy_receipt():
    record = signed_record()
    with pytest.raises(LookupError):
        find_verified_publication(
            "flop_labs", [{**record, "text": record["text"] + "!"}],
            did=record["from"], nonce=record["nonce"], text=record["text"],
            signature=record["sig"]
        )


def test_invalid_signature_cannot_create_receipt():
    record = signed_record()
    bad = {**record, "sig": "A" * len(record["sig"])}
    with pytest.raises(LookupError):
        find_verified_publication(
            "flop_labs", [bad], did=bad["from"], nonce=bad["nonce"],
            text=bad["text"], signature=bad["sig"]
        )
