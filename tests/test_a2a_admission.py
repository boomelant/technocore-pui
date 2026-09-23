"""Regression tests for fail-closed A2A admission until a real executor exists."""

import pytest

from pui.opportunity import Opportunity, discover_latest_executable_opportunity
from pui.opportunity_task import build_task_from_opportunity


def offer(proto, seq=1):
    return Opportunity(
        seq=seq, sender="did:key:z6MkExample", offer_id=f"offer-{seq}",
        amount="1", asset="FLOP", rails=("paper",), job_proto=proto,
        job_context="/kv/context", expires_ms=None,
    )


def test_a2a_builder_rejects_before_untrusted_context_fetch():
    def must_not_fetch(path):
        raise AssertionError("A2A context must not be fetched by BlockRewards builder")

    with pytest.raises(ValueError, match="unsupported task protocol: a2a"):
        build_task_from_opportunity(offer("a2a"), must_not_fetch)


def test_a2a_discovery_never_marks_context_executable(monkeypatch):
    import pui.opportunity as opportunities

    monkeypatch.setattr(opportunities, "parse_tclk_offer", lambda msg: offer("a2a"))
    monkeypatch.setattr(opportunities, "evaluate_opportunity", lambda op: {"eligible": True})

    def must_not_fetch(path):
        raise AssertionError("unsupported A2A must not enter BlockRewards evaluator")

    result = discover_latest_executable_opportunity(
        lambda room, limit: {"messages": [{"seq": 1}]}, must_not_fetch,
    )
    assert result["status"] == "none"
    assert result["opportunity"] is None


def test_unknown_protocol_builder_rejects_before_io():
    with pytest.raises(ValueError, match="unsupported task protocol"):
        build_task_from_opportunity(offer("unknown"), lambda path: 1 / 0)
