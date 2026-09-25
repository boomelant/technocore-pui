"""Time-bound observations without pretending stale evidence is current."""


def classify_freshness(*, observed_at: int, now: int, max_age: int) -> str:
    if any(type(x) is not int for x in (observed_at, now, max_age)):
        raise ValueError("timestamps and age must be exact integers")
    if observed_at < 0 or now < 0 or max_age < 0:
        raise ValueError("negative time or age")
    if observed_at > now:
        return "FUTURE_UNTRUSTED"
    if now - observed_at > max_age:
        return "STALE"
    return "FRESH"
