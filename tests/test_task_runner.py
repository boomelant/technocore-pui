from pui import task_ledger
from pui.task_runner import process_queue_event, process_next_queue_event


def test_process_queue_event_writes_verified_receipt(tmp_path):
    task_ledger.LEDGER_PATH = tmp_path / "task-receipts.jsonl"

    event = {
        "event_key": "lobby:999",
        "room": "lobby",
        "seq": 999,
        "text": "PUI runner test",
        "policy": "REVIEW",
        "execute": False,
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
        "policy": "REVIEW",
        "execute": False,
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
                '{"event_key":"lobby:1","room":"lobby","seq":1,"text":"first","policy":"REVIEW","execute":false}',
                '{"event_key":"lobby:2","room":"lobby","seq":2,"text":"second","policy":"REVIEW","execute":false}',
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


def test_process_queue_event_rejects_ineligible_event(tmp_path):
    task_ledger.LEDGER_PATH = tmp_path / "task-receipts.jsonl"

    event = {
        "event_key": "lobby:2000",
        "room": "lobby",
        "seq": 2000,
        "text": "unsafe direct execution",
        "policy": "AUTO",
        "execute": True,
    }

    result = process_queue_event(event)

    assert result["status"] == "ineligible"
    assert result["written"] is False
    assert not task_ledger.LEDGER_PATH.exists()
