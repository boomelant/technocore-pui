from __future__ import annotations

from datetime import datetime


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_probe(room: str, message: dict) -> dict | None:
    text = message.get("text")

    if not isinstance(text, str):
        return None

    stripped = text.strip()

    if not stripped.lower().startswith("probe v1 |"):
        return None

    parts = [part.strip() for part in stripped.split("|", 3)]

    if len(parts) != 4:
        return None

    prefix, probe_id, condition, body = parts

    if prefix.lower() != "probe v1":
        return None

    if not probe_id:
        return None

    if not condition:
        return None

    sender = message.get("from")
    seq = message.get("seq")
    ts = message.get("ts")

    if not isinstance(sender, str):
        return None

    if not isinstance(seq, int):
        return None

    if not isinstance(ts, str):
        return None

    return {
        "room": room,
        "seq": seq,
        "probe_id": probe_id,
        "condition": condition.lower(),
        "sender": sender,
        "ts": ts,
        "body": body,
        "text": stripped,
    }


def collect_response_candidates(
    probe: dict,
    messages: list[dict],
    window_seconds: int = 120,
) -> dict:
    probe_ts = _parse_ts(probe["ts"])
    probe_seq = probe["seq"]
    probe_sender = probe["sender"]

    responses = []

    for message in messages:
        seq = message.get("seq")
        sender = message.get("from")
        ts = message.get("ts")

        if not isinstance(seq, int):
            continue

        if seq <= probe_seq:
            continue

        if not isinstance(sender, str) or sender == probe_sender:
            continue

        if not isinstance(ts, str):
            continue

        message_ts = _parse_ts(ts)
        latency_ms = int((message_ts - probe_ts).total_seconds() * 1000)

        if latency_ms < 0:
            continue

        if latency_ms > window_seconds * 1000:
            continue

        responses.append({
            "seq": seq,
            "sender": sender,
            "ts": ts,
            "latency_ms": latency_ms,
            "text": message.get("text"),
        })

    responses.sort(key=lambda item: (item["latency_ms"], item["seq"]))

    responders = {item["sender"] for item in responses}

    first_latency = (
        responses[0]["latency_ms"]
        if responses
        else None
    )

    return {
        "candidate_response_count": len(responses),
        "unique_responders": len(responders),
        "first_response_latency_ms": first_latency,
        "responses": responses,
    }


def is_explicit_probe_response(
    probe: dict,
    message: dict,
) -> bool:
    if probe.get("condition") != "ask":
        return False

    probe_id = probe.get("probe_id")
    probe_sender = probe.get("sender")

    sender = message.get("from")
    text = message.get("text")

    if not isinstance(probe_id, str) or not probe_id:
        return False

    if not isinstance(sender, str):
        return False

    if sender == probe_sender:
        return False

    if not isinstance(text, str):
        return False

    return probe_id in text
