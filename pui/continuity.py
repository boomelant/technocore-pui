"""Fail-closed cursor continuity for externally supplied room observations."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Cursor:
    epoch: str
    seq: int

    def __post_init__(self):
        if not isinstance(self.epoch, str) or not self.epoch:
            raise ValueError("epoch required")
        if type(self.seq) is not int or self.seq < 0:
            raise ValueError("nonnegative integer seq required")


def advance(checkpoint: Cursor, *, epoch: str, seq: int) -> tuple[str, Cursor]:
    """Never advance a durable checkpoint over an unobserved record."""
    if not isinstance(epoch, str) or not epoch or type(seq) is not int or seq < 0:
        raise ValueError("invalid observation")
    if epoch != checkpoint.epoch:
        return "STALE_EPOCH", checkpoint
    if seq <= checkpoint.seq:
        return "DUPLICATE", checkpoint
    if seq != checkpoint.seq + 1:
        return "STALE_GAP", checkpoint
    return "CONTIGUOUS", Cursor(epoch, seq)
