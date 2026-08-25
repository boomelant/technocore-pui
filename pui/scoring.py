import hashlib
import re
from collections import Counter
from typing import Any


URL_RE = re.compile(r"https?://\\S+", re.IGNORECASE)
DID_RE = re.compile(r"^did:key:")


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = URL_RE.sub("<url>", text)
    text = re.sub(r"\\b[0-9a-f]{16,}\\b", "<hex>", text)
    text = re.sub(r"(?<![0-9])[0-9]+(?![0-9])", "<number>", text)
    text = re.sub(r"\\s+", " ", text)
    return text


def template_fingerprint(text: str) -> str:
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def analyze_messages(messages: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(messages)

    if total == 0:
        return {
            "messages": 0,
            "signal_score": 0.0,
            "coordination_risk": 100.0,
        }

    authors = [str(m.get("from", "")) for m in messages]
    texts = [str(m.get("text", "")) for m in messages]

    signed = sum(1 for author in authors if DID_RE.match(author))
    unique_authors = len(set(authors))

    templates = Counter(template_fingerprint(text) for text in texts)
    author_counts = Counter(authors)

    top_template_count = templates.most_common(1)[0][1]
    top_author_count = author_counts.most_common(1)[0][1]

    repeated_messages = sum(
        count
        for count in templates.values()
        if count > 1
    )

    one_shot_authors = sum(
        1
        for count in author_counts.values()
        if count == 1
    )

    signed_ratio = signed / total
    author_diversity = unique_authors / total
    template_concentration = top_template_count / total
    repetition_ratio = repeated_messages / total
    author_concentration = top_author_count / total
    one_shot_ratio = one_shot_authors / max(unique_authors, 1)
    author_spread = 1.0 - author_concentration

    quality = (
        0.10 * signed_ratio
        + 0.15 * author_diversity
        + 0.30 * (1.0 - repetition_ratio)
        + 0.25 * (1.0 - template_concentration)
        + 0.10 * (1.0 - author_concentration)
        + 0.10 * (1.0 - one_shot_ratio)
    )

    coordination_risk = (
        0.45 * repetition_ratio * author_spread
        + 0.25 * template_concentration * author_spread
        + 0.20 * one_shot_ratio
        + 0.10 * author_diversity
    )

    signal_score = max(0.0, min(100.0, quality * 100.0))
    coordination_risk = max(0.0, min(100.0, coordination_risk * 100.0))

    return {
        "messages": total,
        "signed_messages": signed,
        "signed_ratio": round(signed_ratio, 4),
        "unique_authors": unique_authors,
        "author_diversity": round(author_diversity, 4),
        "one_shot_authors": one_shot_authors,
        "one_shot_ratio": round(one_shot_ratio, 4),
        "top_template_count": top_template_count,
        "template_concentration": round(template_concentration, 4),
        "repetition_ratio": round(repetition_ratio, 4),
        "top_author_count": top_author_count,
        "author_concentration": round(author_concentration, 4),
        "signal_score": round(signal_score, 2),
        "coordination_risk": round(coordination_risk, 2),
    }
