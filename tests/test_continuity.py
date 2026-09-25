import pytest
from pui.continuity import Cursor, advance


def test_contiguous_advances_once():
    assert advance(Cursor("e1", 4), epoch="e1", seq=5) == ("CONTIGUOUS", Cursor("e1", 5))


def test_gap_never_advances_checkpoint():
    checkpoint = Cursor("e1", 4)
    assert advance(checkpoint, epoch="e1", seq=6) == ("STALE_GAP", checkpoint)


def test_epoch_change_fails_closed():
    checkpoint = Cursor("e1", 4)
    assert advance(checkpoint, epoch="e2", seq=5) == ("STALE_EPOCH", checkpoint)


def test_replay_does_not_advance():
    checkpoint = Cursor("e1", 4)
    assert advance(checkpoint, epoch="e1", seq=4) == ("DUPLICATE", checkpoint)


@pytest.mark.parametrize("bad", [True, -1, 1.0, "1"])
def test_invalid_sequence_rejected(bad):
    with pytest.raises(ValueError):
        advance(Cursor("e1", 0), epoch="e1", seq=bad)
