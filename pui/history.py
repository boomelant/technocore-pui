import json
from collections import Counter
from pathlib import Path

from .scoring import template_fingerprint


def load_snapshot(path: str | Path) -> dict:
    return json.loads(
        Path(path).read_text(encoding="utf-8")
    )


def extract_signals(snapshot: dict) -> dict:
    dids = set()
    templates = Counter()
    did_rooms = {}
    room_counts = {}

    for room, messages in snapshot["rooms"].items():
        room_counts[room] = len(messages)

        for message in messages:
            author = str(message.get("from", ""))
            text = str(message.get("text", ""))

            if not author.startswith("did:key:"):
                continue

            dids.add(author)

            if author not in did_rooms:
                did_rooms[author] = set()

            did_rooms[author].add(room)

            fp = template_fingerprint(text)
            templates[fp] += 1

    return {
        "dids": dids,
        "templates": templates,
        "did_rooms": did_rooms,
        "room_counts": room_counts,
    }


def compare_snapshots(old_snapshot: dict, new_snapshot: dict) -> dict:
    old = extract_signals(old_snapshot)
    new = extract_signals(new_snapshot)

    recurring_dids = old["dids"] & new["dids"]

    recurring_templates = (
        set(old["templates"]) &
        set(new["templates"])
    )

    persistent_patterns = []

    for fp in recurring_templates:
        old_count = old["templates"][fp]
        new_count = new["templates"][fp]

        if old_count < 3 or new_count < 3:
            continue

        persistent_patterns.append({
            "fingerprint": fp,
            "old_count": old_count,
            "new_count": new_count,
            "combined_count": old_count + new_count,
        })

    persistent_patterns.sort(
        key=lambda x: x["combined_count"],
        reverse=True,
    )

    recurring_cross_room = []

    for did in recurring_dids:
        old_rooms = old["did_rooms"].get(did, set())
        new_rooms = new["did_rooms"].get(did, set())
        combined = old_rooms | new_rooms

        if len(combined) < 2:
            continue

        recurring_cross_room.append({
            "did": did,
            "rooms": sorted(combined),
            "room_count": len(combined),
        })

    recurring_cross_room.sort(
        key=lambda x: x["room_count"],
        reverse=True,
    )

    return {
        "old_dids": len(old["dids"]),
        "new_dids": len(new["dids"]),
        "recurring_dids": len(recurring_dids),
        "recurring_did_ratio": round(
            len(recurring_dids) / max(len(new["dids"]), 1),
            4,
        ),
        "recurring_templates": len(recurring_templates),
        "persistent_patterns": persistent_patterns,
        "recurring_cross_room": recurring_cross_room,
    }
