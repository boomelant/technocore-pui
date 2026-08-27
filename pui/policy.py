from dataclasses import dataclass


@dataclass
class PolicyDecision:
    policy: str
    execute: bool
    reason: str


AUTO_CATEGORIES = {
    "faucet",
    "task",
    "testnet_action",
}


def decide_policy(
    category: str,
    confidence: float,
    source_trust: str,
) -> PolicyDecision:

    if source_trust == "unknown":
        return PolicyDecision(
            policy="BLOCKED",
            execute=False,
            reason="Unknown source identity",
        )

    if source_trust == "untrusted":
        return PolicyDecision(
            policy="REVIEW",
            execute=False,
            reason="Actionable event from untrusted DID",
        )

    if source_trust == "trusted":
        if category in AUTO_CATEGORIES and confidence >= 0.90:
            return PolicyDecision(
                policy="REVIEW",
                execute=False,
                reason="Trusted high-confidence event; execution still requires approval",
            )

        return PolicyDecision(
            policy="REVIEW",
            execute=False,
            reason="Trusted source but event is not auto-eligible",
        )

    return PolicyDecision(
        policy="BLOCKED",
        execute=False,
        reason="Unsupported trust state",
    )
