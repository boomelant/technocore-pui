from collections import defaultdict
from typing import Any

from .scoring import template_fingerprint


def build_activity_graph(
    room_messages: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    did_templates = defaultdict(set)
    template_dids = defaultdict(set)
    template_rooms = defaultdict(set)
    did_rooms = defaultdict(set)

    total_messages = 0

    for room, messages in room_messages.items():
        for message in messages:
            author = str(message.get("from", ""))
            text = str(message.get("text", ""))

            if not author.startswith("did:key:"):
                continue

            fp = template_fingerprint(text)

            did_templates[author].add(fp)
            template_dids[fp].add(author)
            template_rooms[fp].add(room)
            did_rooms[author].add(room)

            total_messages += 1

    return {
        "total_signed_messages": total_messages,
        "did_count": len(did_templates),
        "template_count": len(template_dids),
        "did_templates": {
            did: sorted(values)
            for did, values in did_templates.items()
        },
        "template_dids": {
            fp: sorted(values)
            for fp, values in template_dids.items()
        },
        "template_rooms": {
            fp: sorted(values)
            for fp, values in template_rooms.items()
        },
        "did_rooms": {
            did: sorted(values)
            for did, values in did_rooms.items()
        },
    }


def suspicious_templates(
    graph: dict[str, Any],
    min_dids: int = 5,
) -> list[dict[str, Any]]:
    results = []

    for fp, dids in graph["template_dids"].items():
        if len(dids) < min_dids:
            continue

        rooms = graph["template_rooms"].get(fp, [])

        results.append({
            "fingerprint": fp,
            "did_count": len(dids),
            "room_count": len(rooms),
            "rooms": rooms,
            "dids": dids,
        })

    results.sort(
        key=lambda x: (x["did_count"], x["room_count"]),
        reverse=True,
    )

    return results
