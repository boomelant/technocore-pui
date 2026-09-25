"""Bounded, fail-closed reconciliation of caller-owned signed nonces."""


def next_nonce(*, local: int, authoritative_floor: int) -> int:
    """Choose a nonce strictly above both observed floors; caller must sign anew."""
    if type(local) is not int or type(authoritative_floor) is not int:
        raise ValueError("nonce floors must be exact integers")
    if local < 0 or authoritative_floor < 0 or max(local, authoritative_floor) >= 2**63 - 1:
        raise ValueError("nonce floor outside supported range")
    return max(local, authoritative_floor) + 1


def reconcile_once(*, attempted: int, server_floor: int, conflict: bool) -> int:
    """Only an authenticated nonce conflict permits one fresh signing attempt."""
    if conflict is not True:
        raise ValueError("reconciliation requires an authenticated nonce conflict")
    if type(attempted) is not int or type(server_floor) is not int or server_floor < attempted:
        raise ValueError("server floor must not precede attempted nonce")
    return next_nonce(local=attempted, authoritative_floor=server_floor)
