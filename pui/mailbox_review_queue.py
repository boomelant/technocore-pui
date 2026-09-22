import json
from datetime import datetime, timezone
from pathlib import Path

from pui.mailbox import MailboxEvaluation


MAILBOX_REVIEW_PATH = Path("data/mailbox-review-queue.jsonl")


def mailbox_review_key(record: dict) -> str:
    room = record.get("room", "unknown")
    seq = record.get("seq")
    return f"{room}:{seq}"


def load_mailbox_review_keys() -> set[str]:
    if not MAILBOX_REVIEW_PATH.exists():
        return set()

    keys = set()

    with MAILBOX_REVIEW_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            key = item.get("review_key")
            if key:
                keys.add(key)

    return keys


def queue_mailbox_review(
    record: dict,
    evaluation: MailboxEvaluation,
) -> bool:
    if evaluation.policy == "IGNORE":
        return False

    key = mailbox_review_key(record)

    if key in load_mailbox_review_keys():
        return False

    entry = {
        "review_key": key,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "priority": evaluation.priority,
        "room": record.get("room"),
        "seq": record.get("seq"),
        "ts": record.get("ts"),
        "from": record.get("from"),
        "text": record.get("text"),
        "category": evaluation.category,
        "confidence": evaluation.confidence,
        "source_trust": evaluation.source_trust,
        "reason": evaluation.reason,
        "execute": False,
    }

    MAILBOX_REVIEW_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with MAILBOX_REVIEW_PATH.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(
                entry,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        )

    return True
