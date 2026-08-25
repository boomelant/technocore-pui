import base64
import hashlib
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


MULTICODEC_ED25519_PUB = bytes([0xED, 0x01])

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58decode(value: str) -> bytes:
    num = 0
    for char in value:
        num = num * 58 + BASE58_ALPHABET.index(char)

    raw = num.to_bytes((num.bit_length() + 7) // 8, "big") if num else b""

    leading = 0
    for char in value:
        if char == "1":
            leading += 1
        else:
            break

    return b"\x00" * leading + raw


def did_to_public_key(did: str) -> Ed25519PublicKey:
    prefix = "did:key:z"

    if not did.startswith(prefix):
        raise ValueError("unsupported DID format")

    decoded = b58decode(did[len(prefix):])

    if not decoded.startswith(MULTICODEC_ED25519_PUB):
        raise ValueError("DID is not an Ed25519 public key")

    public_bytes = decoded[len(MULTICODEC_ED25519_PUB):]

    if len(public_bytes) != 32:
        raise ValueError("invalid Ed25519 public key length")

    return Ed25519PublicKey.from_public_bytes(public_bytes)


def canonical_json(value) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def verify_report(path: str) -> None:
    report_path = Path(path)

    report = json.loads(report_path.read_text(encoding="utf-8"))

    signature_text = report.get("signature")
    signer = report.get("author")
    expected_hash = report.get("report_hash")

    if not signature_text:
        raise ValueError("report has no signature")

    if not signer:
        raise ValueError("report has no author DID")

    if not expected_hash:
        raise ValueError("report has no report_hash")

    signed_record = dict(report)
    signed_record.pop("signature", None)

    unsigned_record = dict(signed_record)
    unsigned_record.pop("report_hash", None)

    calculated_hash = "sha256:" + hashlib.sha256(
        canonical_json(unsigned_record).encode("utf-8")
    ).hexdigest()

    if calculated_hash != expected_hash:
        raise ValueError(
            f"hash mismatch: expected {expected_hash}, calculated {calculated_hash}"
        )

    padding = "=" * (-len(signature_text) % 4)
    signature = base64.urlsafe_b64decode(signature_text + padding)

    public_key = did_to_public_key(signer)

    public_key.verify(
        signature,
        canonical_json(signed_record).encode("utf-8"),
    )

    print("REPORT VERIFIED")
    print("file:", report_path)
    print("author:", signer)
    print("hash:", expected_hash)
    print("signature:", "valid")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m pui.verify <report.json>")

    verify_report(sys.argv[1])


if __name__ == "__main__":
    main()
