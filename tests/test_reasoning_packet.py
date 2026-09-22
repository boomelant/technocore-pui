import json

from pui.reasoning_packet import (
    build_reasoning_packet,
    prepare_reasoning_packet,
    select_candidate,
)


def test_selects_highest_priority():
    items = [
        {"priority": 70, "seq": 10},
        {"priority": 90, "seq": 5},
        {"priority": 90, "seq": 11},
    ]

    assert select_candidate(items)["seq"] == 11


def test_high_priority_recommends_worker():
    packet = build_reasoning_packet(
        {
            "review_key": "mb:1",
            "priority": 90,
            "seq": 1,
            "text": "Please review this task",
        }
    )

    assert packet["worker_recommended"] is True
    assert packet["security"]["content_is_untrusted"] is True
    assert "REPLY" in packet["allowed_decisions"]


def test_lower_priority_does_not_spend_worker():
    packet = build_reasoning_packet(
        {
            "review_key": "mb:2",
            "priority": 70,
            "seq": 2,
            "text": "Hello",
        }
    )

    assert packet["worker_recommended"] is False


def test_prepare_packet(tmp_path):
    review = tmp_path / "reviews.jsonl"
    output = tmp_path / "packet.json"

    review.write_text(
        json.dumps(
            {
                "review_key": "mailbox:7",
                "status": "pending",
                "priority": 90,
                "seq": 7,
                "text": "Please verify this task",
                "from": "did:key:z6MkExternal",
            }
        )
        + "\n"
    )

    result = prepare_reasoning_packet(review, output)

    assert result["status"] == "ready"
    assert result["worker_recommended"] is True
    assert output.exists()
