"""Read-only verifier for Technocore signed message read-back.

Usage: python scripts/verify_technocore_readback.py ROOM SEQ < room.json
Never sends a POST or loads a signing seed.
Requires cryptography (Ed25519 public-key verification only).
"""
import base64
import json
import sys

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58decode(value):
    n = 0
    for ch in value:
        n = n * 58 + ALPHABET.index(ch)
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\x00" * (len(value) - len(value.lstrip("1"))) + raw


def verify(room, record):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    did, sig, nonce, message = (record[k] for k in ("from", "sig", "nonce", "text"))
    if not isinstance(did, str) or not did.startswith("did:key:z"):
        raise ValueError("not an Ed25519 did:key")
    decoded = b58decode(did[len("did:key:z"):])
    if len(decoded) != 34 or decoded[:2] != b"\xed\x01":
        raise ValueError("invalid Ed25519 multicodec")
    if not isinstance(nonce, (str, int)) or not str(nonce).isdigit() or len(str(nonce)) > 19:
        raise ValueError("invalid nonce")
    if not isinstance(sig, str) or len(sig) != 86 or not isinstance(message, str):
        raise ValueError("invalid signed record")
    signature = base64.urlsafe_b64decode(sig + "==")
    if len(signature) != 64 or base64.urlsafe_b64encode(signature).decode().rstrip("=") != sig:
        raise ValueError("noncanonical signature")
    Ed25519PublicKey.from_public_bytes(decoded[2:]).verify(
        signature, f"{room}|{nonce}|{message}".encode("utf-8")
    )
    return did


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: verify_technocore_readback.py ROOM SEQ < room.json")
    room, seq = sys.argv[1], int(sys.argv[2])
    payload = json.load(sys.stdin)
    records = payload if isinstance(payload, list) else payload.get("messages", [])
    matches = [r for r in records if int(r.get("seq", -1)) == seq]
    if len(matches) != 1:
        raise SystemExit("FAIL: requested room+seq absent or ambiguous")
    did = verify(room, matches[0])
    print(f"PASS room={room} seq={seq} did={did}")


if __name__ == "__main__":
    main()
