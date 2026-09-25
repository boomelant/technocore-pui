import pytest
from pui.nonce_floor import next_nonce, reconcile_once


def test_restart_with_high_server_floor():
    assert next_nonce(local=12, authoritative_floor=10**12) == 10**12 + 1


def test_local_floor_above_server():
    assert next_nonce(local=100, authoritative_floor=10) == 101


def test_authenticated_conflict_advances():
    assert reconcile_once(attempted=10, server_floor=11, conflict=True) == 12


def test_non_conflict_never_recovers():
    with pytest.raises(ValueError):
        reconcile_once(attempted=10, server_floor=11, conflict=False)


@pytest.mark.parametrize("floor", [True, -1, 1.5, 2**63 - 1])
def test_bad_floor_fails_closed(floor):
    with pytest.raises(ValueError):
        next_nonce(local=0, authoritative_floor=floor)
