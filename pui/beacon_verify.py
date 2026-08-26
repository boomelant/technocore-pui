import base64
import json
import sys
from pathlib import Path

from pui.protocol import canonical_json
from pui.verify import did_to_public_key


def verify_beacon(path):
    beacon_path = Path(path)
    beacon = json.loads(beacon_path.read_text(encoding="utf-8"))

    signature_text = beacon.get("signature")
    did = beacon.get("did")

    if not signature_text:
        raise ValueError("beacon has no signature")

    if not did:
        raise ValueError("beacon has no did")

    signed = dict(beacon)
    signed.pop("signature", None)

    padding = "=" * (-len(signature_text) % 4)
    signature = base64.urlsafe_b64decode(signature_text + padding)

    key = did_to_public_key(did)

    key.verify(
        signature,
        canonical_json(signed).encode("utf-8"),
    )

    print("BEACON VERIFIED")
    print("file:", beacon_path)
    print("did:", did)
    print("release:", beacon.get("release"))
    print("technocore room:", beacon.get("technocore_room"))
    print("technocore seq:", beacon.get("technocore_seq"))
    print("report hash:", beacon.get("report_hash"))
    print("signature:", "valid")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m pui.beacon_verify <beacon.json>")

    verify_beacon(sys.argv[1])


if __name__ == "__main__":
    main()
