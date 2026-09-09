import pytest

from pui.opportunity import Opportunity
from pui.opportunity_task import task_from_blockrewards_opportunity


def test_task_from_blockrewards_opportunity():
    opportunity = Opportunity(
        seq=123,
        sender="did:key:z6MkExample",
        offer_id="0xabc",
        amount="200",
        asset="FLOP",
        rails=("paper",),
        job_proto="blockrewards",
        job_context="/kv/tclk-job/example",
        expires_ms=None,
    )

    task = task_from_blockrewards_opportunity(
        opportunity,
        "census | difficulty 1/3 | source=/kv/tclk-mat/example",
    )

    assert task.task_id == "tclk:0xabc"
    assert task.task_type == "blockrewards_census"
    assert task.payload["offer_id"] == "0xabc"
    assert task.payload["source_seq"] == 123
    assert task.payload["source_sender"] == "did:key:z6MkExample"
    assert task.payload["job_context_path"] == "/kv/tclk-job/example"


def test_task_from_blockrewards_rejects_wrong_proto():
    opportunity = Opportunity(
        seq=123,
        sender="did:key:z6MkExample",
        offer_id="0xabc",
        amount="200",
        asset="FLOP",
        rails=("paper",),
        job_proto="a2a",
        job_context="/kv/tclk-job/example",
        expires_ms=None,
    )

    with pytest.raises(ValueError, match="not blockrewards"):
        task_from_blockrewards_opportunity(
            opportunity,
            "example",
        )


def test_build_task_from_opportunity_fetches_context():
    from pui.opportunity_task import build_task_from_opportunity

    opportunity = Opportunity(
        seq=321,
        sender="did:key:z6MkExample",
        offer_id="0xdef",
        amount="400",
        asset="FLOP",
        rails=("paper",),
        job_proto="blockrewards",
        job_context="/kv/tclk-job/def",
        expires_ms=None,
    )

    def fake_get_text(path):
        if path == "/kv/tclk-job/def":
            return (
                "census | difficulty 1/3 | "
                "source /kv/tclk-mat-67/example"
            )

        if path == "/kv/tclk-mat-67/example":
            return (
                "seq | id | payer | amount | asset | rails | proto | role "
                "1 | 0xaaa | Alice | 200 | FLOP | paper | blockrewards | payer"
            )

        raise AssertionError(f"unexpected path: {path}")

    task = build_task_from_opportunity(
        opportunity,
        fake_get_text,
    )

    assert task.task_id == "tclk:0xdef"
    assert task.task_type == "blockrewards_census"
    assert "/kv/tclk-mat-67/example" == task.payload["material_path"]
    assert "Alice" in task.payload["material_text"]


def test_task_from_blockrewards_math_opportunity():
    from pui.opportunity import Opportunity
    from pui.opportunity_task import task_from_blockrewards_math_opportunity

    opportunity = Opportunity(
        seq=123,
        sender="did:key:z6MkExample",
        offer_id="0xmath",
        amount="200",
        asset="FLOP",
        rails=("paper",),
        job_proto="blockrewards",
        job_context="/kv/tclk-job-1d/math-example",
        expires_ms=None,
    )

    context = (
        "math | [difficulty 1/3] "
        "Compute gcd(10, 20) and lcm(10, 20)."
    )

    task = task_from_blockrewards_math_opportunity(
        opportunity,
        context,
    )

    assert task.task_id == "tclk:0xmath"
    assert task.task_type == "blockrewards_math"
    assert task.payload["source_seq"] == 123
    assert task.payload["source_sender"] == "did:key:z6MkExample"
    assert task.payload["job_context_path"] == "/kv/tclk-job-1d/math-example"
    assert task.payload["job_context_text"] == context


def test_build_task_from_opportunity_builds_math_task():
    from pui.opportunity_task import build_task_from_opportunity

    opportunity = Opportunity(
        seq=456,
        sender="did:key:z6MkMath",
        offer_id="0xmath2",
        amount="200",
        asset="FLOP",
        rails=("paper",),
        job_proto="blockrewards",
        job_context="/kv/tclk-job/math2",
        expires_ms=None,
    )

    def fake_get_text(path):
        if path == "/kv/tclk-job/math2":
            return (
                "math | [difficulty 1/3] "
                "Compute gcd(10, 20) and lcm(10, 20)."
            )

        raise AssertionError(f"unexpected path: {path}")

    task = build_task_from_opportunity(
        opportunity,
        fake_get_text,
    )

    assert task.task_id == "tclk:0xmath2"
    assert task.task_type == "blockrewards_math"
    assert task.payload["job_context_path"] == "/kv/tclk-job/math2"
    assert "gcd(10, 20)" in task.payload["job_context_text"]
