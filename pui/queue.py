import json
from pathlib import Path

from pui.decision import evaluate_event


QUEUE_PATH = Path("data/agent-queue.jsonl")


def event_key(record: dict) -> str:
    room = record.get("room", "unknown")
    seq = record.get("seq")
    return f"{room}:{seq}"


def load_seen_keys() -> set[str]:
    if not QUEUE_PATH.exists():
        return set()

    seen = set()

    with QUEUE_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            key = entry.get("event_key")
            if key:
                seen.add(key)

    return seen


def queue_event(record: dict) -> bool:
    evaluation = evaluate_event(record)

    if evaluation.policy == "IGNORE":
        return False

    key = event_key(record)

    if key in load_seen_keys():
        return False

    entry = {
        "event_key": key,
        "room": record.get("room"),
        "seq": record.get("seq"),
        "ts": record.get("ts"),
        "from": record.get("from"),
        "text": record.get("text"),
        "category": evaluation.category,
        "confidence": evaluation.confidence,
        "source_trust": evaluation.source_trust,
        "policy": evaluation.policy,
        "execute": evaluation.execute,
        "reason": evaluation.reason,
    }

    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with QUEUE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                entry,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n"
        )

    return True
