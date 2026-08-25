import re
from collections import defaultdict
from itertools import combinations
from typing import Any

from .scoring import normalize_text


WORD_RE = re.compile(r"[a-z0-9_-]+", re.IGNORECASE)


def tokens(text: str) -> set[str]:
    normalized = normalize_text(text)
    return set(WORD_RE.findall(normalized))


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0

    union = a | b
    if not union:
        return 0.0

    return len(a & b) / len(union)


def find_lexical_clusters(
    room_messages: dict[str, list[dict[str, Any]]],
    threshold: float = 0.72,
    min_dids: int = 4,
) -> list[dict[str, Any]]:
    records = []

    for room, messages in room_messages.items():
        for message in messages:
            author = str(message.get("from", ""))
            text = str(message.get("text", ""))

            if not author.startswith("did:key:"):
                continue

            records.append({
                "room": room,
                "did": author,
                "text": text,
                "tokens": tokens(text),
            })

    parent = list(range(len(records)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra = find(a)
        rb = find(b)
        if ra != rb:
            parent[rb] = ra

    buckets = defaultdict(list)

    for i, record in enumerate(records):
        first_tokens = sorted(record["tokens"])[:3]
        bucket = "|".join(first_tokens)
        buckets[bucket].append(i)

    for indices in buckets.values():
        if len(indices) < 2:
            continue

        for i, j in combinations(indices, 2):
            score = jaccard(records[i]["tokens"], records[j]["tokens"])

            if score >= threshold:
                union(i, j)

    groups = defaultdict(list)

    for i in range(len(records)):
        groups[find(i)].append(records[i])

    results = []

    for group in groups.values():
        dids = sorted({item["did"] for item in group})

        if len(dids) < min_dids:
            continue

        rooms = sorted({item["room"] for item in group})

        results.append({
            "did_count": len(dids),
            "message_count": len(group),
            "room_count": len(rooms),
            "rooms": rooms,
            "example": group[0]["text"][:180],
        })

    results.sort(
        key=lambda x: (
            x["did_count"],
            x["room_count"],
            x["message_count"],
        ),
        reverse=True,
    )

    return results


def did_cross_room_activity(
    room_messages: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    did_rooms = defaultdict(set)
    did_messages = defaultdict(int)

    for room, messages in room_messages.items():
        for message in messages:
            author = str(message.get("from", ""))

            if not author.startswith("did:key:"):
                continue

            did_rooms[author].add(room)
            did_messages[author] += 1

    results = []

    for did, rooms in did_rooms.items():
        if len(rooms) < 2:
            continue

        results.append({
            "did": did,
            "room_count": len(rooms),
            "rooms": sorted(rooms),
            "messages": did_messages[did],
        })

    results.sort(
        key=lambda x: (x["room_count"], x["messages"]),
        reverse=True,
    )

    return results
