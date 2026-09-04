import json
from pathlib import Path

from .task_receipt import TaskReceipt


LEDGER_PATH = Path("data/task-receipts.jsonl")


def receipt_exists(task_id: str) -> bool:
    if not LEDGER_PATH.exists():
        return False

    with LEDGER_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)

            if record.get("task_id") == task_id:
                return True

    return False


def append_task_receipt(receipt: TaskReceipt) -> bool:
    if receipt_exists(receipt.task_id):
        return False

    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)

    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                receipt.to_dict(),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            )
            + "\n"
        )

    return True
