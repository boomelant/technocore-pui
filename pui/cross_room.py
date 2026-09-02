import json
from collections import defaultdict
from pathlib import Path

ROOMS = (
    "lobby",
    "technocore",
    "meta",
    "flop-network",
    "inference-agents",
)

DATA_DIR = Path("data/chronicle")


def top_cross_room_dids(limit: int = 20) -> list[dict]:
    activity = defaultdict(
        lambda: {
            "rooms": set(),
            "messages": 0,
        }
    )

    for room in ROOMS:
        path = DATA_DIR / f"{room}.jsonl"

        if not path.exists():
            continue

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                record = json.loads(line)
                did = record.get("from")

                if not isinstance(did, str) or not did.startswith("did:key:"):
                    continue

                activity[did]["rooms"].add(room)
                activity[did]["messages"] += 1

    rows = []

    for did, stats in activity.items():
        if len(stats["rooms"]) < 2:
            continue

        rows.append(
            {
                "did": did,
                "rooms_seen": sorted(stats["rooms"]),
                "room_count": len(stats["rooms"]),
                "messages": stats["messages"],
            }
        )

    rows.sort(
        key=lambda row: (
            row["room_count"],
            row["messages"],
            row["did"],
        ),
        reverse=True,
    )

    return rows[:limit]
