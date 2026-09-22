import json

import pui.mailbox
import pui.mailbox_review_queue
import pui.queue


ROOT = "did:key:z6MkRoot"
OTHER = "did:key:z6MkExternal"


def test_mailbox_event_goes_to_dedicated_queue(tmp_path, monkeypatch):
    mailbox_path = tmp_path / "mailbox-review.jsonl"
    agent_path = tmp_path / "agent-queue.jsonl"

    monkeypatch.setattr(
        pui.mailbox_review_queue,
        "MAILBOX_REVIEW_PATH",
        mailbox_path,
    )
    monkeypatch.setattr(
        pui.queue,
        "QUEUE_PATH",
        agent_path,
    )
    monkeypatch.setattr(
        pui.mailbox,
        "public_did",
        lambda: ROOT,
    )

    record = {
        "room": "mb-p-pui-test",
        "seq": 7,
        "ts": "2026-09-22T08:00:00Z",
        "from": OTHER,
        "sig": "signature",
        "nonce": "123",
        "text": "Please review this task",
    }

    assert pui.queue.queue_event(record) is True

    assert mailbox_path.exists()
    assert not agent_path.exists()

    entry = json.loads(mailbox_path.read_text().strip())

    assert entry["review_key"] == "mb-p-pui-test:7"
    assert entry["priority"] == 90
    assert entry["status"] == "pending"
    assert entry["execute"] is False


def test_mailbox_event_is_deduplicated(tmp_path, monkeypatch):
    mailbox_path = tmp_path / "mailbox-review.jsonl"

    monkeypatch.setattr(
        pui.mailbox_review_queue,
        "MAILBOX_REVIEW_PATH",
        mailbox_path,
    )
    monkeypatch.setattr(
        pui.mailbox,
        "public_did",
        lambda: ROOT,
    )

    record = {
        "room": "mb-p-pui-test",
        "seq": 8,
        "from": OTHER,
        "sig": "signature",
        "nonce": "456",
        "text": "Can you help verify this?",
    }

    assert pui.queue.queue_event(record) is True
    assert pui.queue.queue_event(record) is False
