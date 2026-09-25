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
