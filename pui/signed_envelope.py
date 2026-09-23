"""Independent verification of signed Technocore room records.

Technocore room messages are signed over the exact UTF-8 payload
``room|nonce|text``.  Verification never needs access to the local private key.
"""
import base64

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


# did:key Ed25519 public keys use the multicodec prefix 0xed01, then 32 key bytes.
_ED25519_MULTICODEC = b"\xed\x01"
_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _b58decode(value: str) -> bytes:
    if not value or any(ch not in _B58_ALPHABET for ch in value):
        raise ValueError("invalid base58btc")
    number = 0
    for ch in value:
        number = number * 58 + _B58_ALPHABET.index(ch)
    body = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    zeros = len(value) - len(value.lstrip("1"))
    return b"\x00" * zeros + body


def ed25519_public_key_from_did(did: str) -> Ed25519PublicKey:
    if not isinstance(did, str) or not did.startswith("did:key:z"):
        raise ValueError("expected did:key with base58btc multibase")
    decoded = _b58decode(did[len("did:key:z"):])
    if not decoded.startswith(_ED25519_MULTICODEC):
        raise ValueError("DID is not an Ed25519 public key")
    raw = decoded[len(_ED25519_MULTICODEC):]
    if len(raw) != 32:
        raise ValueError("invalid Ed25519 public key length")
    return Ed25519PublicKey.from_public_bytes(raw)


def _urlsafe_b64decode_unpadded(value: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError("signature required")
    try:
        return base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid signature encoding") from exc


def verify_room_envelope(room: str, record: dict) -> bool:
    """Return True only when the exact server envelope has a valid signature.

    Required record fields are ``from``, ``nonce``, ``text`` and ``sig``.  The
    nonce is converted to text without numeric coercion, preserving large
    decimal values supplied by the venue.
    """
    if not isinstance(room, str) or not room:
        raise ValueError("room required")
    if not isinstance(record, dict):
        raise ValueError("record required")
    did = record.get("from")
    nonce = record.get("nonce")
    text = record.get("text")
    sig = record.get("sig")
    if not isinstance(nonce, str) or not nonce.isdecimal():
        raise ValueError("nonce must be exact decimal text")
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    signature = _urlsafe_b64decode_unpadded(sig)
    if len(signature) != 64:
        raise ValueError("invalid Ed25519 signature length")
    payload = f"{room}|{nonce}|{text}".encode("utf-8")
    try:
        ed25519_public_key_from_did(did).verify(signature, payload)
    except InvalidSignature:
        return False
    return True
