from dataclasses import dataclass

from .action import execute_reviewed_message


@dataclass
class ReviewRequest:
    room: str
    text: str
    approved: bool = False


def execute_review_request(request: ReviewRequest):
    return execute_reviewed_message(
        request.room,
        request.text,
        approved=request.approved,
    )
