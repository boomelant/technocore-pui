import pytest
from pui.evidence_freshness import classify_freshness


def test_age_boundary_inclusive():
    assert classify_freshness(observed_at=10, now=20, max_age=10) == "FRESH"
    assert classify_freshness(observed_at=10, now=21, max_age=10) == "STALE"


def test_future_observation_not_fresh():
    assert classify_freshness(observed_at=21, now=20, max_age=10) == "FUTURE_UNTRUSTED"


def test_bool_timestamp_rejected():
    with pytest.raises(ValueError):
        classify_freshness(observed_at=True, now=20, max_age=10)
