import json
from pathlib import Path

from pui.agent_state import get_last_processed, set_last_processed
from pui.queue import queue_event


DATA_DIR = Path("data/chronicle")

ROOMS = [
    "lobby",
    "technocore",
    "meta",
    "flop-network",
    "inference-agents",
]


def scan_room(room: str) -> tuple[int, int, int | None]:
    path = DATA_DIR / f"{room}.jsonl"

    if not path.exists():
        return 0, 0, None

    last_processed = get_last_processed(room)

    scanned = 0
    queued = 0
    highest_seq = last_processed

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            seq = record.get("seq")

            if not isinstance(seq, int):
                continue

            if last_processed is not None and seq <= last_processed:
                continue

            record["room"] = room
            scanned += 1

            if queue_event(record):
                queued += 1

            if highest_seq is None or seq > highest_seq:
                highest_seq = seq

    if highest_seq is not None and highest_seq != last_processed:
        set_last_processed(room, highest_seq)

    return scanned, queued, highest_seq


def main():
    total_scanned = 0
    total_queued = 0

    for room in ROOMS:
        scanned, queued, last_seq = scan_room(room)

        total_scanned += scanned
        total_queued += queued

        print(
            room,
            "scanned:",
            scanned,
            "queued:",
            queued,
            "last_processed:",
            last_seq,
        )

    print()
    print("TOTAL SCANNED:", total_scanned)
    print("NEW QUEUED:", total_queued)


if __name__ == "__main__":
    main()
