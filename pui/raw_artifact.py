"""Digest exact producer bytes; never hash a parsed-and-reserialized artifact."""
import hashlib


def describe_artifact(raw: bytes) -> dict:
    if type(raw) is not bytes:
        raise ValueError("artifact must be raw bytes")
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError("artifact exceeds bounded verification size")
    return {"sha256": hashlib.sha256(raw).hexdigest(), "size": len(raw)}


def verify_artifact(raw: bytes, *, sha256: str, size: int) -> bool:
    if type(size) is not int or size < 0 or not isinstance(sha256, str) or len(sha256) != 64:
        raise ValueError("invalid artifact descriptor")
    return describe_artifact(raw) == {"sha256": sha256, "size": size}
