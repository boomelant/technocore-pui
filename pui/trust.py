from dataclasses import dataclass


@dataclass
class TrustDecision:
    level: str
    policy: str
    reason: str


TRUSTED_DIDS: set[str] = set()


def evaluate_source(source_did: str | None) -> TrustDecision:
    if not source_did:
        return TrustDecision(
            level="unknown",
            policy="BLOCKED",
            reason="Message has no source DID",
        )

    if source_did in TRUSTED_DIDS:
        return TrustDecision(
            level="trusted",
            policy="REVIEW",
            reason="Source DID is explicitly trusted",
        )

    if source_did.startswith("did:key:"):
        return TrustDecision(
            level="untrusted",
            policy="REVIEW",
            reason="Valid-looking DID source but not on trusted list",
        )

    return TrustDecision(
        level="unknown",
        policy="BLOCKED",
        reason="Source is not a recognized DID",
    )
