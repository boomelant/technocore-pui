import pytest
from pui.evidence_axes import Evidence


def test_terminal_transport_is_not_work_acceptance():
    e = Evidence("VERIFIED_TERMINAL", "UNKNOWN", "ABSENT", "claimed")
    assert e.work_accepted is False


def test_refund_never_counts_as_accepted_work():
    e = Evidence("VERIFIED_TERMINAL", "MATCH", "VERIFIED", "refunded")
    assert e.work_accepted is False


def test_all_three_positive_axes_required():
    e = Evidence("VERIFIED_TERMINAL", "MATCH", "VERIFIED", "claimed")
    assert e.work_accepted is True


def test_unconfirmed_transport_cannot_claim_terminal():
    with pytest.raises(ValueError):
        Evidence("UNCONFIRMED", "UNKNOWN", "UNKNOWN", "claimed")


def test_invalid_evidence_label_rejected():
    with pytest.raises(ValueError):
        Evidence("SUCCESS", "MATCH", "VERIFIED", "claimed")
