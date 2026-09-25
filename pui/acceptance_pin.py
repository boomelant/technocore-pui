"""Bind an issuer's acceptance to independently expected task and artifact pins."""
import hmac
import re

_SHA = re.compile(r"[0-9a-f]{64}")


def acceptance_matches(*, expected_task: str, expected_artifact: str, declared_task: str,
                       declared_artifact: str, signature_verified: bool) -> bool:
    if not isinstance(expected_task, str) or not expected_task or not isinstance(declared_task, str):
        raise ValueError("task identity required")
    if not all(isinstance(x, str) and _SHA.fullmatch(x) for x in (expected_artifact, declared_artifact)):
        raise ValueError("valid SHA-256 pins required")
    return (signature_verified is True and hmac.compare_digest(expected_task, declared_task)
            and hmac.compare_digest(expected_artifact, declared_artifact))
