from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from .identity import public_did
from .technocore import read_room, send_signed_message


@dataclass
class ActionReceipt:
    status: str
    room: str
    seq: int | None
    did: str
    text: str
    verified: bool
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)


def execute_reviewed_message(
    room: str,
    text: str,
    *,
    approved: bool = False,
) -> ActionReceipt:
    if not approved:
        raise PermissionError("Action requires explicit REVIEW approval")

    did = public_did()

    send_signed_message(room, text)

    data = read_room(room, limit=200)
    messages = data.get("messages", [])

    match = None

    for message in reversed(messages):
        if (
            message.get("from") == did
            and message.get("text") == text
        ):
            match = message
            break

    return ActionReceipt(
        status="executed" if match else "unverified",
        room=room,
        seq=match.get("seq") if match else None,
        did=did,
        text=text,
        verified=match is not None,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
