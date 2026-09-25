"""Classify room admission without confusing listable and total room counts."""


def classify_capacity(*, total: int | None, capacity: int, listed: int | None = None) -> str:
    if type(capacity) is not int or capacity <= 0:
        raise ValueError("positive capacity required")
    if total is None:
        return "UNKNOWN"
    if type(total) is not int or total < 0:
        raise ValueError("invalid authoritative total")
    if listed is not None and (type(listed) is not int or listed < 0 or listed > total):
        raise ValueError("listed rooms cannot exceed total rooms")
    return "SATURATED" if total >= capacity else "HEADROOM"
