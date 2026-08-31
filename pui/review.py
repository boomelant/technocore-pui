from dataclasses import dataclass

from .action import execute_reviewed_message
from .receipts import append_receipt


@dataclass
class ReviewRequest:
    room: str
    text: str
    approved: bool = False


def execute_review_request(request: ReviewRequest):
    receipt = execute_reviewed_message(
        request.room,
        request.text,
        approved=request.approved,
    )

    append_receipt(receipt)

    return receipt
