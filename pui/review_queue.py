import json
from datetime import datetime, timezone
from pathlib import Path


REVIEW_QUEUE_PATH = Path("data/review-queue.jsonl")


def load_review_keys() -> set[str]:
    if not REVIEW_QUEUE_PATH.exists():
        return set()

    keys = set()

    with REVIEW_QUEUE_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            key = record.get("review_key")

            if key:
                keys.add(key)

    return keys


def queue_review_action(
    *,
    review_key: str,
    source: str,
    room: str,
    text: str,
    reason: str,
    metadata: dict | None = None,
) -> bool:
    if not review_key:
        raise ValueError("review_key is required")

    if not room:
        raise ValueError("room is required")

    if not text:
        raise ValueError("text is required")

    if review_key in load_review_keys():
        return False

    record = {
        "review_key": review_key,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "source": source,
        "room": room,
        "text": text,
        "reason": reason,
        "metadata": metadata or {},
        "approved": False,
    }

    REVIEW_QUEUE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with REVIEW_QUEUE_PATH.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(
                record,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        )

    return True
