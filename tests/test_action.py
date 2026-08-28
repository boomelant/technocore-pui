import pytest

from pui.action import execute_reviewed_message


def test_action_requires_explicit_review_approval():
    with pytest.raises(PermissionError, match="requires explicit REVIEW approval"):
        execute_reviewed_message(
            "lobby",
            "dry test",
            approved=False,
        )
