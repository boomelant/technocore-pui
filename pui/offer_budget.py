"""Bound untrusted offer sizes before parsing or running expensive solvers."""


def admit_offer(raw: bytes, *, max_bytes: int = 65536) -> str:
    if type(max_bytes) is not int or not 1 <= max_bytes <= 1048576:
        raise ValueError("invalid offer size limit")
    if type(raw) is not bytes or not raw or len(raw) > max_bytes:
        raise ValueError("offer is empty, non-bytes, or over budget")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("offer must be valid UTF-8") from exc
    if "\x00" in text:
        raise ValueError("offer contains NUL")
    return text
