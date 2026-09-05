from pui import task_ledger
from pui.task_runner import process_queue_event, process_next_queue_event


def test_process_queue_event_writes_verified_receipt(tmp_path):
    task_ledger.LEDGER_PATH = tmp_path / "task-receipts.jsonl"

    event = {
        "event_key": "lobby:999",
        "room": "lobby",
        "seq": 999,
        "text": "PUI runner test",
    }

    result = process_queue_event(event)

    assert result["status"] == "completed"
    assert result["verified"] is True
    assert result["written"] is True
    assert result["task_id"] == "queue:lobby:999"
    assert task_ledger.LEDGER_PATH.exists()


def test_process_queue_event_is_idempotent(tmp_path):
    task_ledger.LEDGER_PATH = tmp_path / "task-receipts.jsonl"

    event = {
        "event_key": "lobby:1000",
        "room": "lobby",
        "seq": 1000,
        "text": "PUI duplicate test",
    }

    first = process_queue_event(event)
    second = process_queue_event(event)

    assert first["status"] == "completed"
    assert second["status"] == "duplicate"
    assert second["written"] is False


def test_process_next_queue_event_uses_latest_unprocessed(tmp_path):
    queue_path = tmp_path / "agent-queue.jsonl"
    task_ledger.LEDGER_PATH = tmp_path / "task-receipts.jsonl"

    queue_path.write_text(
        "\n".join(
            [
                '{"event_key":"lobby:1","room":"lobby","seq":1,"text":"first"}',
                '{"event_key":"lobby:2","room":"lobby","seq":2,"text":"second"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    first = process_next_queue_event(queue_path)
    second = process_next_queue_event(queue_path)

    assert first["task_id"] == "queue:lobby:2"
    assert first["status"] == "completed"
    assert second["task_id"] == "queue:lobby:1"
    assert second["status"] == "completed"
