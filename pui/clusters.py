from collections import defaultdict
from typing import Any

from .scoring import template_fingerprint, normalize_text


def find_template_clusters(
    messages: list[dict[str, Any]],
    min_authors: int = 3,
) -> list[dict[str, Any]]:
    clusters = defaultdict(lambda: {
        "authors": set(),
        "messages": [],
        "example": "",
    })

    for message in messages:
        author = str(message.get("from", ""))
        text = str(message.get("text", ""))

        fp = template_fingerprint(text)

        cluster = clusters[fp]
        cluster["authors"].add(author)
        cluster["messages"].append(message)

        if not cluster["example"]:
            cluster["example"] = normalize_text(text)[:180]

    results = []

    for fingerprint, cluster in clusters.items():
        author_count = len(cluster["authors"])
        message_count = len(cluster["messages"])

        if author_count < min_authors:
            continue

        results.append({
            "fingerprint": fingerprint,
            "authors": sorted(cluster["authors"]),
            "author_count": author_count,
            "message_count": message_count,
            "example": cluster["example"],
        })

    results.sort(
        key=lambda item: (
            item["author_count"],
            item["message_count"],
        ),
        reverse=True,
    )

    return results
