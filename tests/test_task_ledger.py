from pathlib import Path

import pui.task_ledger as task_ledger
from pui.task_receipt import TaskReceipt


def test_append_task_receipt_is_idempotent(tmp_path):
    task_ledger.LEDGER_PATH = tmp_path / "task-receipts.jsonl"

    receipt = TaskReceipt(
        task_id="queue:lobby:123",
        task_type="text_analysis",
        status="completed",
        input_hash="sha256:input",
        result_hash="sha256:result",
        verified=True,
        created_at="2026-09-04T00:00:00+00:00",
    )

    assert task_ledger.append_task_receipt(receipt) is True
    assert task_ledger.append_task_receipt(receipt) is False

    lines = task_ledger.LEDGER_PATH.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
