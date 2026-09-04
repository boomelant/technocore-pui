import pytest

from pui.task_adapter import task_from_queue_event


def test_queue_event_becomes_text_analysis_task():
    event = {
        "event_key": "lobby:123",
        "room": "lobby",
        "seq": 123,
        "text": "untrusted room message",
        "policy": "REVIEW",
        "execute": False,
    }

    task = task_from_queue_event(event)

    assert task.task_id == "queue:lobby:123"
    assert task.task_type == "text_analysis"
    assert task.payload["text"] == "untrusted room message"
    assert task.payload["source_event_key"] == "lobby:123"
    assert task.payload["source_room"] == "lobby"
    assert task.payload["source_seq"] == 123


def test_queue_event_requires_integer_seq():
    event = {
        "event_key": "lobby:123",
        "room": "lobby",
        "seq": "123",
        "text": "message",
    }

    with pytest.raises(ValueError, match="integer seq"):
        task_from_queue_event(event)
