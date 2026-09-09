import re
from collections import Counter


ROW_PATTERN = re.compile(
    r'(\d+)\s+\|\s+(0x[0-9a-f]+)\s+\|\s+([A-Za-z0-9]+)\s+\|\s+'
    r'(\d+)\s+\|\s+([A-Z]+)\s+\|\s+([^|]+)\s+\|\s+([^|]+)\s+\|\s+([a-z]+)'
)


def solve_census(material_text: str) -> dict:
    if not isinstance(material_text, str) or not material_text.strip():
        raise ValueError("material text is required")

    rows = ROW_PATTERN.findall(material_text)

    if not rows:
        raise ValueError("no census rows found")

    payers = [
        row[2]
        for row in rows
        if row[7].strip() == "payer"
    ]

    if not payers:
        raise ValueError("no payer rows found")

    counts = Counter(payers)
    top_count = max(counts.values())
    top_payer = sorted(
        payer
        for payer, count in counts.items()
        if count == top_count
    )[0]

    answer = (
        f"offers={len(rows)}; "
        f"payers={len(counts)}; "
        f"top={top_payer}:{top_count}"
    )

    return {
        "offers": len(rows),
        "payers": len(counts),
        "top_payer": top_payer,
        "top_count": top_count,
        "answer": answer,
    }


MATERIAL_PATH_PATTERN = re.compile(r'(/kv/tclk-mat-[A-Za-z0-9_-]+/[A-Za-z0-9_-]+)')


def extract_material_path(job_context_text: str) -> str:
    if not isinstance(job_context_text, str) or not job_context_text.strip():
        raise ValueError("job context text is required")

    match = MATERIAL_PATH_PATTERN.search(job_context_text)

    if match is None:
        raise ValueError("material path not found")

    return match.group(1)


def classify_job_context(job_context_text: str) -> str:
    if not isinstance(job_context_text, str) or not job_context_text.strip():
        return "unknown"

    text = job_context_text.lower()

    if "census" in text and "/kv/tclk-mat-" in text:
        return "census"

    if "fold this tclk/1 transcript" in text or "foldtranscript" in text:
        return "protocol_fold"

    if text.lstrip().startswith("math |"):
        return "math"

    if text.lstrip().startswith("validation |"):
        return "validation"

    if text.lstrip().startswith("verification |"):
        return "verification"

    return "unsupported"


MATH_GCD_LCM_PATTERN = re.compile(
    r'compute\s+gcd\((\d+),\s*(\d+)\)\s+and\s+lcm\(\1,\s*\2\)',
    re.IGNORECASE,
)


def solve_math(job_context_text: str) -> dict:
    import math

    if not isinstance(job_context_text, str) or not job_context_text.strip():
        raise ValueError("math job context is required")

    match = MATH_GCD_LCM_PATTERN.search(job_context_text)

    if match is None:
        raise ValueError("unsupported math task")

    a = int(match.group(1))
    b = int(match.group(2))

    gcd_value = math.gcd(a, b)
    lcm_value = math.lcm(a, b)

    return {
        "gcd": gcd_value,
        "lcm": lcm_value,
        "answer": f"gcd={gcd_value} lcm={lcm_value}",
    }


def supports_math_job(job_context_text: str) -> bool:
    if not isinstance(job_context_text, str):
        return False

    return MATH_GCD_LCM_PATTERN.search(job_context_text) is not None


TCLK_FRAME_PATTERN = re.compile(
    r'(tclk-offers|mb-p-tclk-[0-9a-f]{16})\s+\|\s+'
    r'([^|]+?)\s+\|\s+'
    r'(did:key:[A-Za-z0-9]+)\s+\|\s+'
    r'(tclk1\s+\{.*?\})'
)


def extract_tclk_transcript(job_context_text: str) -> list[dict]:
    import json

    if not isinstance(job_context_text, str) or not job_context_text.strip():
        raise ValueError("job context is required")

    header_pattern = re.compile(
        r'(tclk-offers|mb-p-tclk-[0-9a-f]{16})\s+\|\s+'
        r'([^|]+?)\s+\|\s+'
        r'(did:key:[A-Za-z0-9]+)\s+\|\s+'
        r'tclk1\s+'
    )

    decoder = json.JSONDecoder()
    records = []

    for match in header_pattern.finditer(job_context_text):
        json_start = match.end()

        try:
            payload, consumed = decoder.raw_decode(
                job_context_text[json_start:]
            )
        except json.JSONDecodeError as exc:
            raise ValueError("invalid tclk transcript json") from exc

        frame_json = job_context_text[
            json_start:json_start + consumed
        ]

        records.append(
            {
                "room": match.group(1).strip(),
                "timestamp": match.group(2).strip(),
                "sender": match.group(3).strip(),
                "frame": f"tclk1 {frame_json}",
            }
        )

    if not records:
        raise ValueError("no tclk transcript records found")

    return records

def parse_tclk_transcript(job_context_text: str) -> list[dict]:
    import json

    records = extract_tclk_transcript(job_context_text)
    parsed = []

    for record in records:
        frame = record["frame"]

        if not frame.startswith("tclk1 "):
            raise ValueError("invalid tclk frame prefix")

        try:
            payload = json.loads(frame[6:])
        except json.JSONDecodeError as exc:
            raise ValueError("invalid tclk frame json") from exc

        if not isinstance(payload, dict):
            raise ValueError("tclk frame payload must be an object")

        frame_type = payload.get("type")

        if not isinstance(frame_type, str) or not frame_type:
            raise ValueError("tclk frame type is required")

        parsed.append(
            {
                "room": record["room"],
                "timestamp": record["timestamp"],
                "sender": record["sender"],
                "type": frame_type,
                "payload": payload,
            }
        )

    return parsed


def fold_tclk_transcript(job_context_text: str) -> dict:
    records = parse_tclk_transcript(job_context_text)

    status = "proposed"
    rejected = []
    contract = None

    for record in records:
        frame_type = record["type"]
        payload = record["payload"]
        room = record["room"]

        if (
            frame_type in {"offer", "accept"}
            or contract is None
        ):
            expected_room = "tclk-offers"
        else:
            expected_room = f"mb-p-tclk-{contract[2:18]}"

        if room != expected_room:
            rejected.append(
                {
                    "type": frame_type,
                    "reason": (
                        f"{frame_type} must be posted in "
                        f"{expected_room}"
                    ),
                }
            )
            continue

        if frame_type == "offer":
            if status != "proposed":
                rejected.append(
                    {
                        "type": frame_type,
                        "reason": f"offer invalid from state {status}",
                    }
                )

        elif frame_type == "accept":
            if status != "proposed":
                rejected.append(
                    {
                        "type": frame_type,
                        "reason": f"accept invalid from state {status}",
                    }
                )
            else:
                status = "accepted"
                contract = payload.get("contract")

        elif frame_type == "lock":
            if status != "accepted":
                rejected.append(
                    {
                        "type": frame_type,
                        "reason": f"lock invalid from state {status}",
                    }
                )
            else:
                status = "locked"

        elif frame_type == "reveal":
            if status != "locked":
                rejected.append(
                    {
                        "type": frame_type,
                        "reason": f"reveal invalid from state {status}",
                    }
                )
            else:
                status = "claimed"

        elif frame_type == "refund":
            if status != "locked":
                rejected.append(
                    {
                        "type": frame_type,
                        "reason": f"refund invalid from state {status}",
                    }
                )
            else:
                status = "refunded"

        elif frame_type == "cancel":
            if status not in {"proposed", "accepted"}:
                rejected.append(
                    {
                        "type": frame_type,
                        "reason": f"cancel invalid from state {status}",
                    }
                )
            else:
                status = "cancelled"

        elif frame_type == "heartbeat":
            if status not in {"accepted", "locked"}:
                rejected.append(
                    {
                        "type": frame_type,
                        "reason": f"heartbeat invalid from state {status}",
                    }
                )

        elif frame_type == "receipt":
            if status not in {"claimed", "refunded", "cancelled"}:
                rejected.append(
                    {
                        "type": frame_type,
                        "reason": "receipt before a terminal status",
                    }
                )

        else:
            rejected.append(
                {
                    "type": frame_type,
                    "reason": "unsupported frame type",
                }
            )

    return {
        "status": status,
        "rejected": rejected,
    }


def format_protocol_fold_answer(result: dict) -> str:
    status = result.get("status")
    rejected = result.get("rejected")

    if not isinstance(status, str) or not status:
        raise ValueError("fold status is required")

    if not isinstance(rejected, list):
        raise ValueError("fold rejected list is required")

    if not rejected:
        return f"{status}\nno rejected records"

    first = rejected[0]

    frame_type = first.get("type", "record")
    reason = first.get("reason", "rejected")

    return (
        f"{status}\n"
        f"{frame_type} rejected: {reason}"
    )


VERIFICATION_LOCK_COUNT_PATTERN = re.compile(
    r'how many rows are lock frames posted by '
    r'(did:key:[A-Za-z0-9]+)\?',
    re.IGNORECASE,
)

VERIFICATION_ROW_PATTERN = re.compile(
    r'(\d+)\s+\|\s+'
    r'(\d{1,2}:\d{2})\s+\|\s+'
    r'(offer|accept|lock|reveal|receipt|refund|cancel|heartbeat)\s+\|\s+'
    r'(did:key:[A-Za-z0-9]+)\s+\|\s+'
    r'([^|]+?)(?=\s+\d+\s+\|\s+\d{1,2}:\d{2}\s+\||$)',
    re.IGNORECASE,
)


def supports_verification_lock_count(job_context_text: str) -> bool:
    if not isinstance(job_context_text, str):
        return False

    return (
        VERIFICATION_LOCK_COUNT_PATTERN.search(job_context_text)
        is not None
    )


def solve_verification_lock_count(
    job_context_text: str,
    material_text: str,
) -> dict:
    if not isinstance(job_context_text, str) or not job_context_text.strip():
        raise ValueError("verification job context is required")

    if not isinstance(material_text, str) or not material_text.strip():
        raise ValueError("verification material text is required")

    match = VERIFICATION_LOCK_COUNT_PATTERN.search(job_context_text)

    if match is None:
        raise ValueError("unsupported verification task")

    target_did = match.group(1)

    rows = VERIFICATION_ROW_PATTERN.findall(material_text)

    if not rows:
        raise ValueError("no verification rows found")

    count = sum(
        1
        for row in rows
        if row[2].lower() == "lock"
        and row[3] == target_did
    )

    return {
        "target_did": target_did,
        "count": count,
        "answer": str(count),
    }
