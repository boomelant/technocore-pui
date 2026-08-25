import hashlib
import json
import time
import uuid
from typing import Any


PUI_VERSION = "PUI/1"


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def timestamp_ms() -> int:
    return int(time.time() * 1000)


def make_request(
    requester: str,
    task: str,
    capability: str,
) -> dict[str, Any]:
    payload = {
        "pui": PUI_VERSION,
        "type": "request",
        "id": new_id("req"),
        "requester": requester,
        "task": task.strip(),
        "capability": capability.strip().lower(),
        "created_at": timestamp_ms(),
        "challenge": uuid.uuid4().hex,
    }
    payload["hash"] = sha256_text(canonical_json(payload))
    return payload


def make_response(
    request: dict[str, Any],
    provider: str,
    result: str,
) -> dict[str, Any]:
    payload = {
        "pui": PUI_VERSION,
        "type": "response",
        "id": new_id("res"),
        "request_id": request["id"],
        "request_hash": request["hash"],
        "provider": provider,
        "result_hash": sha256_text(result),
        "created_at": timestamp_ms(),
    }
    payload["hash"] = sha256_text(canonical_json(payload))
    return payload


def make_receipt(
    request: dict[str, Any],
    response: dict[str, Any],
    receiver: str,
    useful: bool,
    score: int,
    reason: str,
) -> dict[str, Any]:
    if not 0 <= score <= 100:
        raise ValueError("score must be between 0 and 100")

    payload = {
        "pui": PUI_VERSION,
        "type": "receipt",
        "id": new_id("rcp"),
        "request_id": request["id"],
        "request_hash": request["hash"],
        "response_id": response["id"],
        "response_hash": response["hash"],
        "provider": response["provider"],
        "receiver": receiver,
        "capability": request["capability"],
        "useful": useful,
        "score": score,
        "reason": reason.strip(),
        "created_at": timestamp_ms(),
    }
    payload["hash"] = sha256_text(canonical_json(payload))
    return payload
