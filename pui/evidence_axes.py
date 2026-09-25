"""Independent evidence dimensions: transport is not work acceptance."""
from dataclasses import dataclass

TRANSPORT = frozenset({"VERIFIED_TERMINAL", "UNCONFIRMED", "UNKNOWN"})
DELIVERABLE = frozenset({"MATCH", "MISMATCH", "UNKNOWN"})
ACCEPTANCE = frozenset({"VERIFIED", "ABSENT", "UNKNOWN"})


@dataclass(frozen=True)
class Evidence:
    transport: str
    deliverable: str
    acceptance: str
    terminal_status: str | None = None

    def __post_init__(self):
        if self.transport not in TRANSPORT or self.deliverable not in DELIVERABLE or self.acceptance not in ACCEPTANCE:
            raise ValueError("invalid evidence dimension")
        if self.transport == "VERIFIED_TERMINAL" and self.terminal_status not in {"claimed", "refunded", "cancelled"}:
            raise ValueError("verified terminal status required")
        if self.transport != "VERIFIED_TERMINAL" and self.terminal_status is not None:
            raise ValueError("unverified transport cannot assert terminal status")

    @property
    def work_accepted(self) -> bool:
        return (self.transport == "VERIFIED_TERMINAL" and self.terminal_status == "claimed"
                and self.deliverable == "MATCH" and self.acceptance == "VERIFIED")
