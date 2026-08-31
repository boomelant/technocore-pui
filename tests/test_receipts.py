import json

from pui.action import ActionReceipt
from pui.review import ReviewRequest, execute_review_request
import pui.review as review_module
import pui.receipts as receipts_module


def test_review_persists_receipt(monkeypatch, tmp_path):
    receipt = ActionReceipt(
        status="executed",
        room="lobby",
        seq=123,
        did="did:key:test",
        text="test action",
        verified=True,
        created_at="2026-08-31T00:00:00+00:00",
    )

    monkeypatch.setattr(
        review_module,
        "execute_reviewed_message",
        lambda *args, **kwargs: receipt,
    )

    test_path = tmp_path / "action-receipts.jsonl"
    monkeypatch.setattr(receipts_module, "RECEIPTS_PATH", test_path)

    request = ReviewRequest(
        room="lobby",
        text="test action",
        approved=True,
    )

    result = execute_review_request(request)

    assert result == receipt

    saved = json.loads(test_path.read_text(encoding="utf-8").strip())

    assert saved["seq"] == 123
    assert saved["verified"] is True
    assert saved["room"] == "lobby"
