import json
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Opportunity:
    seq: int
    sender: str
    offer_id: str
    amount: str
    asset: str
    rails: tuple[str, ...]
    job_proto: str | None
    job_context: str | None
    expires_ms: int | None


def parse_tclk_offer(message: dict) -> Opportunity | None:
    text = message.get("text")

    if not isinstance(text, str):
        return None

    if not text.startswith("tclk1 "):
        return None

    try:
        frame = json.loads(text[6:])
    except json.JSONDecodeError:
        return None

    if frame.get("type") != "offer":
        return None

    job = frame.get("job")
    if not isinstance(job, dict):
        job = {}

    rails = frame.get("rails")
    if not isinstance(rails, list):
        rails = []

    return Opportunity(
        seq=int(message["seq"]),
        sender=str(message.get("from", "")),
        offer_id=str(frame.get("id", "")),
        amount=str(frame.get("amount", "")),
        asset=str(frame.get("asset", "")),
        rails=tuple(str(x) for x in rails),
        job_proto=job.get("proto"),
        job_context=job.get("context"),
        expires_ms=frame.get("expiresMs"),
    )


def discover_latest_opportunity(read_room_func, limit: int = 50) -> Opportunity | None:
    data = read_room_func("tclk-offers", limit=limit)

    messages = data.get("messages", [])
    if not isinstance(messages, list):
        return None

    for message in reversed(messages):
        opportunity = parse_tclk_offer(message)
        if opportunity is not None:
            return opportunity

    return None


def evaluate_opportunity(
    opportunity: Opportunity,
    now_ms: int | None = None,
) -> dict:
    if now_ms is None:
        now_ms = time.time_ns() // 1_000_000

    if (
        isinstance(opportunity.expires_ms, int)
        and opportunity.expires_ms <= now_ms
    ):
        return {
            "eligible": False,
            "reason": "expired_offer",
        }

    if opportunity.job_proto != "blockrewards":
        return {
            "eligible": False,
            "reason": "unsupported_job_proto",
        }

    if "paper" not in opportunity.rails:
        return {
            "eligible": False,
            "reason": "unsupported_rail",
        }

    if not opportunity.job_context:
        return {
            "eligible": False,
            "reason": "missing_job_context",
        }

    return {
        "eligible": True,
        "reason": "supported_blockrewards_job",
    }


def discover_and_evaluate(read_room_func, limit: int = 50) -> dict:
    opportunity = discover_latest_opportunity(
        read_room_func,
        limit=limit,
    )

    if opportunity is None:
        return {
            "status": "none",
            "opportunity": None,
            "decision": None,
        }

    decision = evaluate_opportunity(opportunity)

    return {
        "status": "candidate",
        "opportunity": opportunity,
        "decision": decision,
    }


def opportunity_snapshot(read_room_func) -> dict:
    result = discover_and_evaluate(read_room_func)

    opportunity = result.get("opportunity")
    decision = result.get("decision")

    if opportunity is None:
        return {
            "status": result.get("status", "none"),
            "opportunity": None,
            "decision": decision,
        }

    return {
        "status": result.get("status", "candidate"),
        "opportunity": {
            "seq": opportunity.seq,
            "sender": opportunity.sender,
            "offer_id": opportunity.offer_id,
            "amount": opportunity.amount,
            "asset": opportunity.asset,
            "rails": list(opportunity.rails),
            "job_proto": opportunity.job_proto,
            "job_context": opportunity.job_context,
            "expires_ms": opportunity.expires_ms,
        },
        "decision": decision,
    }


def discover_latest_eligible_opportunity(
    read_room_func,
    limit: int = 200,
) -> Opportunity | None:
    data = read_room_func("tclk-offers", limit=limit)

    messages = data.get("messages", [])
    if not isinstance(messages, list):
        return None

    for message in reversed(messages):
        opportunity = parse_tclk_offer(message)
        if opportunity is None:
            continue

        decision = evaluate_opportunity(opportunity)

        if decision.get("eligible") is True:
            return opportunity

    return None


def evaluate_job_context(job_context_text: str) -> dict:
    from .blockrewards import classify_job_context

    job_type = classify_job_context(job_context_text)

    if job_type == "census":
        return {
            "eligible": True,
            "job_type": "census",
            "reason": "supported_blockrewards_census",
        }

    if job_type == "math":
        from .blockrewards import supports_math_job

        if supports_math_job(job_context_text):
            return {
                "eligible": True,
                "job_type": "math",
                "reason": "supported_blockrewards_math",
            }

        return {
            "eligible": False,
            "job_type": "math",
            "reason": "unsupported_math_task",
        }

    if job_type == "verification":
        from .blockrewards import supports_verification_lock_count

        if supports_verification_lock_count(job_context_text):
            return {
                "eligible": True,
                "job_type": "verification_lock_count",
                "reason": "supported_verification_lock_count",
            }

        return {
            "eligible": False,
            "job_type": "verification",
            "reason": "unsupported_verification_task",
        }

    if job_type == "protocol_fold":
        return {
            "eligible": False,
            "job_type": "protocol_fold",
            "reason": "recognized_but_not_implemented",
        }

    return {
        "eligible": False,
        "job_type": job_type,
        "reason": "unsupported_blockrewards_job",
    }


def discover_latest_executable_opportunity(
    read_room_func,
    get_text_func,
    limit: int = 200,
) -> dict:
    data = read_room_func("tclk-offers", limit=limit)

    messages = data.get("messages", [])
    if not isinstance(messages, list):
        return {
            "status": "none",
            "opportunity": None,
            "decision": None,
            "job_context_text": None,
        }

    for message in reversed(messages):
        opportunity = parse_tclk_offer(message)
        if opportunity is None:
            continue

        basic = evaluate_opportunity(opportunity)
        if basic.get("eligible") is not True:
            continue

        if not opportunity.job_context:
            continue

        context_text = get_text_func(opportunity.job_context)
        decision = evaluate_job_context(context_text)

        if decision.get("eligible") is True:
            return {
                "status": "executable",
                "opportunity": opportunity,
                "decision": decision,
                "job_context_text": context_text,
            }

    return {
        "status": "none",
        "opportunity": None,
        "decision": None,
        "job_context_text": None,
    }
