import json
from pathlib import Path

from .action import ActionReceipt

RECEIPTS_PATH = Path("data/action-receipts.jsonl")


def append_receipt(receipt: ActionReceipt) -> None:
    RECEIPTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with RECEIPTS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(receipt.to_dict(), sort_keys=True) + "\n")
