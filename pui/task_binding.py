"""Reader-controlled binding of task, spec and checker hashes."""
import hashlib
import hmac


def binding_status(*, expected_job: str, actual_job: str, expected_spec_sha256: str,
                   spec_bytes: bytes | None, expected_checker_sha256: str,
                   checker_bytes: bytes | None) -> str:
    if not isinstance(expected_job, str) or not expected_job or not isinstance(actual_job, str):
        raise ValueError("job identifiers required")
    for digest in (expected_spec_sha256, expected_checker_sha256):
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("invalid expected digest")
    if not hmac.compare_digest(expected_job, actual_job):
        return "MISMATCH"
    for raw, expected in ((spec_bytes, expected_spec_sha256), (checker_bytes, expected_checker_sha256)):
        if raw is not None and (type(raw) is not bytes or not hmac.compare_digest(hashlib.sha256(raw).hexdigest(), expected)):
            return "MISMATCH"
    if spec_bytes is None or checker_bytes is None:
        return "UNKNOWN"
    return "MATCH"
