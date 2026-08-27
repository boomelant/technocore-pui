from dataclasses import dataclass


@dataclass
class AgentDecision:
    category: str
    policy: str
    confidence: float
    reason: str


RESULT_PHRASES = (
    "status: success",
    "[poui verifiable proof]",
    "verifiable proof",
    "validator:",
    "price | asset:",
    "task allocation:",
)

NOISE_PHRASES = (
    "checking in",
    "check-in complete",
    "node online",
    "agent active",
    "coordination alive",
    "status nominal",
    "telemetry",
    "cycle finished",
    "cycle #",
    "protocol is holding up",
    "standing by for task delegation",
    "autonomous agents need",
    "watching this space",
    "happy to compare notes",
    "completed a coordination step",
    "task orchestration this cycle",
    "task agent exploring",
    "reasoning about task orchestration",
    "signed and present",
)


TASK_DIRECTIVES = (
    "complete this task",
    "complete the task",
    "first agent to",
    "reply with your did",
    "submit your",
    "submit the",
    "create a room",
    "create the room",
    "join the room",
    "your task is",
    "mission:",
)


FAUCET_DIRECTIVES = (
    "claim from the faucet",
    "claim testnet tokens",
    "claim test tokens",
    "get testnet tokens",
    "get test tokens",
    "use the faucet",
    "faucet is live",
    "faucet is available",
)


TESTNET_DIRECTIVES = (
    "connect to the testnet",
    "connect your wallet",
    "deploy to testnet",
    "deploy on testnet",
    "bridge to testnet",
    "mint on testnet",
    "register on testnet",
    "submit on testnet",
)


def contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def classify_text(text: str) -> AgentDecision:
    normalized = text.lower().strip()

    if contains_any(normalized, RESULT_PHRASES):
        return AgentDecision(
            category="result",
            policy="IGNORE",
            confidence=0.95,
            reason="Task result or proof message, not an actionable directive",
        )

    if contains_any(normalized, NOISE_PHRASES):
        return AgentDecision(
            category="noise",
            policy="IGNORE",
            confidence=0.95,
            reason="Routine presence, telemetry, or discussion message",
        )

    if contains_any(normalized, FAUCET_DIRECTIVES):
        return AgentDecision(
            category="faucet",
            policy="REVIEW",
            confidence=0.95,
            reason="Explicit faucet action detected",
        )

    if contains_any(normalized, TESTNET_DIRECTIVES):
        return AgentDecision(
            category="testnet_action",
            policy="REVIEW",
            confidence=0.95,
            reason="Explicit testnet action detected",
        )

    if contains_any(normalized, TASK_DIRECTIVES):
        return AgentDecision(
            category="task",
            policy="REVIEW",
            confidence=0.90,
            reason="Explicit task or challenge directive detected",
        )

    return AgentDecision(
        category="other",
        policy="IGNORE",
        confidence=0.10,
        reason="No explicit actionable directive detected",
    )
