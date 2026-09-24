"""Guard against routing unsupported A2A jobs through BlockRewards execution."""

import pytest

from pui.opportunity import Opportunity, discover_latest_executable_opportunity
from pui.opportunity_task import build_task_from_opportunity


def offer(proto, seq=1):
    return Opportunity(
        seq=seq, sender="did:key:z6MkExample", offer_id=f"offer-{seq}",
        amount="1", asset="FLOP", rails=("paper",), job_proto=proto,
        job_context="/kv/context", expires_ms=None,
    )


def test_a2a_builder_rejected_before_context_fetch():
    def forbidden_fetch(path):
        raise AssertionError("A2A context was fetched by BlockRewards task builder")

    with pytest.raises(ValueError, match="unsupported task protocol: a2a"):
        build_task_from_opportunity(offer("a2a"), forbidden_fetch)


def test_a2a_discovery_skips_context_fetch(monkeypatch):
    import pui.opportunity as opportunities

    monkeypatch.setattr(opportunities, "parse_tclk_offer", lambda msg: offer("a2a"))
    monkeypatch.setattr(opportunities, "evaluate_opportunity", lambda op: {"eligible": True})

    def forbidden_fetch(path):
        raise AssertionError("A2A context entered BlockRewards classifier")

    result = discover_latest_executable_opportunity(
        lambda room, limit: {"messages": [{"seq": 1}]}, forbidden_fetch,
    )
    assert result["status"] == "none"
    assert result["opportunity"] is None


def test_unsupported_protocol_builder_rejected_before_context_fetch():
    with pytest.raises(ValueError, match="unsupported task protocol: unknown"):
        build_task_from_opportunity(offer("unknown"), lambda path: 1 / 0)


def test_supported_blockrewards_math_still_builds_task():
    task = build_task_from_opportunity(
        offer("blockrewards"), lambda path: "math | Compute gcd(12, 18) and lcm(12, 18)",
    )
    assert task.task_type == "blockrewards_math"
