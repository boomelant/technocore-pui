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

    if re.search(r"(?m)^math\s*\|", text):
        return "math"

    if re.search(r"(?m)^validation\s*\|", text):
        return "validation"

    if re.search(r"(?m)^verification\s*\|", text):
        return "verification"

    return "unsupported"


MATH_GCD_LCM_PATTERN = re.compile(
    r'compute\s+gcd\((\d+),\s*(\d+)\)\s+and\s+lcm\(\1,\s*\2\)',
    re.IGNORECASE,
)


MODULAR_INVERSE_PATTERN = re.compile(
    r'find the modular inverse of\s+(\d+)\s+modulo\s+(\d+).*?'
    r'with\s+\1(?:·|\*)x\s*≡\s*1\s*\(mod\s*\2\)',
    re.IGNORECASE | re.DOTALL,
)


# Only explicitly supported single-line prime tasks. 64-bit MR bases provide
# deterministic primality for all n < 2**64; cap work far below that limit.
PRIME_TASK_PATTERN = re.compile(
    r"(?im)^math\s*\|[^\n]*?smallest prime strictly greater than\s+(\d+)\?"
)


def _is_prime_64(n: int) -> bool:
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in (2, 325, 9375, 28178, 450775, 9780504, 1795265022):
        if a % n == 0:
            continue
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _next_prime_bounded(n: int) -> int:
    if n < 0 or n > 10**15:
        raise ValueError("prime task input outside bounded range")
    candidate = n + 1
    if candidate <= 2:
        return 2
    if candidate % 2 == 0:
        candidate += 1
    for _ in range(5000):
        if _is_prime_64(candidate):
            return candidate
        candidate += 2
    raise ValueError("prime search bound exhausted")


def solve_math(job_context_text: str) -> dict:
    import math

    if not isinstance(job_context_text, str) or not job_context_text.strip():
        raise ValueError("math job context is required")

    match = MATH_GCD_LCM_PATTERN.search(job_context_text)

    if match is None:
        inverse = MODULAR_INVERSE_PATTERN.search(job_context_text)
        if inverse is not None:
            a = int(inverse.group(1))
            modulus = int(inverse.group(2))
            if modulus <= 1 or modulus > 10**15:
                raise ValueError("modular inverse input outside bounded range")
            try:
                value = pow(a, -1, modulus)
            except ValueError as exc:
                raise ValueError("modular inverse does not exist") from exc
            return {"inverse": value, "answer": str(value)}

        prime = PRIME_TASK_PATTERN.search(job_context_text)
        if prime is None:
            raise ValueError("unsupported math task")
        result = _next_prime_bounded(int(prime.group(1)))
        return {"prime": result, "answer": str(result)}


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

    inverse = MODULAR_INVERSE_PATTERN.search(job_context_text)
    if inverse is not None:
        modulus = int(inverse.group(2))
        return 1 < modulus <= 10**15

    prime = PRIME_TASK_PATTERN.search(job_context_text)
    if prime is not None:
        return int(prime.group(1)) <= 10**15
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
