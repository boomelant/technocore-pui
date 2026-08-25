import base64
import hashlib
import subprocess

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .config import DID, KEYCHAIN_SERVICE


def load_seed() -> bytes:
    result = subprocess.run(
        [
            "security",
            "find-generic-password",
            "-a",
            subprocess.getoutput("whoami"),
            "-s",
            KEYCHAIN_SERVICE,
            "-w",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    raw = result.stdout.strip()

    try:
        seed = bytes.fromhex(raw)
    except ValueError:
        seed = hashlib.sha256(raw.encode("utf-8")).digest()

    if len(seed) != 32:
        raise ValueError("Seed must resolve to exactly 32 bytes.")

    return seed


def private_key() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(load_seed())


def sign_bytes(payload: bytes) -> str:
    signature = private_key().sign(payload)
    return base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")


def sign_text(text: str) -> str:
    return sign_bytes(text.encode("utf-8"))


def public_did() -> str:
    return DID


def sign_pui_record(record: dict, canonicalizer) -> dict:
    unsigned = dict(record)
    unsigned.pop("signature", None)
    unsigned.pop("signer", None)

    canonical = canonicalizer(unsigned)

    signed = dict(unsigned)
    signed["signer"] = DID
    signed["signature"] = sign_text(canonical)

    return signed
