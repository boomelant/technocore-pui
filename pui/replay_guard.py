"""Bounded replay guard for immutable room/sequence observations."""
from collections import OrderedDict
import re

_SHA256_HEX = re.compile(r"[0-9a-f]{64}")


class ReplayGuard:
    def __init__(self, max_entries: int = 4096):
        if type(max_entries) is not int or not 1 <= max_entries <= 100000:
            raise ValueError("invalid replay window")
        self.max_entries = max_entries
        self._seen = OrderedDict()

    def observe(self, room: str, epoch: str, seq: int, digest: str) -> str:
        if (
            not isinstance(room, str) or not room
            or not isinstance(epoch, str) or not epoch
            or type(seq) is not int or seq < 1
            or not isinstance(digest, str) or _SHA256_HEX.fullmatch(digest) is None
        ):
            raise ValueError("invalid observation")
        key = (room, epoch, seq)
        old = self._seen.get(key)
        if old is not None:
            return "DUPLICATE" if old == digest else "CONFLICT"
        self._seen[key] = digest
        if len(self._seen) > self.max_entries:
            self._seen.popitem(last=False)
        return "NEW"
