import json
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


def evaluate_opportunity(opportunity: Opportunity) -> dict:
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
