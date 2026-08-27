from dataclasses import dataclass

from pui.agent import classify_text
from pui.policy import decide_policy
from pui.trust import evaluate_source


@dataclass
class AgentEvaluation:
    category: str
    confidence: float
    source_trust: str
    policy: str
    execute: bool
    reason: str


def evaluate_event(record: dict) -> AgentEvaluation:
    text = record.get("text", "")
    source_did = record.get("from")

    content = classify_text(text)
    trust = evaluate_source(source_did)

    if content.policy == "IGNORE":
        return AgentEvaluation(
            category=content.category,
            confidence=content.confidence,
            source_trust=trust.level,
            policy="IGNORE",
            execute=False,
            reason=content.reason,
        )

    policy = decide_policy(
        category=content.category,
        confidence=content.confidence,
        source_trust=trust.level,
    )

    return AgentEvaluation(
        category=content.category,
        confidence=content.confidence,
        source_trust=trust.level,
        policy=policy.policy,
        execute=policy.execute,
        reason=f"{content.reason}; {trust.reason}; {policy.reason}",
    )
