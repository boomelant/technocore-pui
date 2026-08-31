import pytest

from pui.review import ReviewRequest, execute_review_request


def test_review_request_respects_approval_guard():
    request = ReviewRequest(
        room="lobby",
        text="dry test",
        approved=False,
    )

    with pytest.raises(PermissionError, match="requires explicit REVIEW approval"):
        execute_review_request(request)
