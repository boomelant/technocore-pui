import pytest

from pui.replay_guard import ReplayGuard


def test_repeated_record_is_idempotent():
    guard = ReplayGuard()
    assert guard.observe("lobby", "e", 1, "a" * 64) == "NEW"
    assert guard.observe("lobby", "e", 1, "a" * 64) == "DUPLICATE"


def test_conflicting_same_sequence_fails_closed():
    guard = ReplayGuard()
    guard.observe("lobby", "e", 1, "a" * 64)
    assert guard.observe("lobby", "e", 1, "b" * 64) == "CONFLICT"


def test_epoch_is_part_of_identity():
    guard = ReplayGuard()
    assert guard.observe("lobby", "e1", 1, "a" * 64) == "NEW"
    assert guard.observe("lobby", "e2", 1, "a" * 64) == "NEW"


def test_bounded_window():
    guard = ReplayGuard(1)
    guard.observe("lobby", "e", 1, "a" * 64)
    guard.observe("lobby", "e", 2, "b" * 64)
    assert guard.observe("lobby", "e", 1, "a" * 64) == "NEW"


@pytest.mark.parametrize("digest", ["g" * 64, "A" * 64, "a" * 63, "a" * 65])
def test_invalid_sha256_digest_is_rejected(digest):
    with pytest.raises(ValueError, match="invalid observation"):
        ReplayGuard().observe("lobby", "e", 1, digest)


@pytest.mark.parametrize(("room", "epoch"), [(None, "e"), ("lobby", None), (1, "e"), ("lobby", 1)])
def test_room_and_epoch_must_be_nonempty_strings(room, epoch):
    with pytest.raises(ValueError, match="invalid observation"):
        ReplayGuard().observe(room, epoch, 1, "a" * 64)
