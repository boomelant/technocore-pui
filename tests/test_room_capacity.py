import pytest
from pui.room_capacity import classify_capacity


def test_listable_rooms_do_not_imply_headroom():
    assert classify_capacity(total=81920, capacity=81920, listed=54391) == "SATURATED"


def test_missing_authoritative_count_is_unknown():
    assert classify_capacity(total=None, capacity=81920, listed=54391) == "UNKNOWN"


def test_authoritative_headroom():
    assert classify_capacity(total=100, capacity=200, listed=90) == "HEADROOM"


def test_impossible_count_is_rejected():
    with pytest.raises(ValueError):
        classify_capacity(total=10, capacity=20, listed=11)
