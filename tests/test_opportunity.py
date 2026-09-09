from pui.opportunity import parse_tclk_offer


def test_parse_tclk_offer():
    message = {
        "seq": 617698,
        "from": "did:key:z6MkExample",
        "text": (
            'tclk1 '
            '{"amount":"200","asset":"FLOP","expiresMs":1788786619573,'
            '"id":"0xabc","job":{"context":"/kv/job/example","proto":"blockrewards"},'
            '"rails":["paper"],"type":"offer"}'
        ),
    }

    opportunity = parse_tclk_offer(message)

    assert opportunity is not None
    assert opportunity.seq == 617698
    assert opportunity.sender == "did:key:z6MkExample"
    assert opportunity.offer_id == "0xabc"
    assert opportunity.amount == "200"
    assert opportunity.asset == "FLOP"
    assert opportunity.rails == ("paper",)
    assert opportunity.job_proto == "blockrewards"
    assert opportunity.job_context == "/kv/job/example"
    assert opportunity.expires_ms == 1788786619573


def test_parse_tclk_offer_rejects_non_offer():
    message = {
        "seq": 1,
        "from": "did:key:z6MkExample",
        "text": 'tclk1 {"type":"accept"}',
    }

    assert parse_tclk_offer(message) is None

def test_discover_latest_opportunity():
    messages = {
        "messages": [
            {
                "seq": 10,
                "from": "did:key:z6MkA",
                "text": 'tclk1 {"type":"accept"}',
            },
            {
                "seq": 11,
                "from": "did:key:z6MkB",
                "text": (
                    'tclk1 '
                    '{"amount":"200","asset":"FLOP","id":"0x123",'
                    '"job":{"context":"/kv/job/latest","proto":"blockrewards"},'
                    '"rails":["paper"],"type":"offer"}'
                ),
            },
        ]
    }

    def fake_read_room(room, limit=50):
        assert room == "tclk-offers"
        return messages

    from pui.opportunity import discover_latest_opportunity

    opportunity = discover_latest_opportunity(fake_read_room)

    assert opportunity is not None
    assert opportunity.seq == 11
    assert opportunity.offer_id == "0x123"
    assert opportunity.job_proto == "blockrewards"

def test_evaluate_opportunity_supported():
    from pui.opportunity import Opportunity, evaluate_opportunity

    opportunity = Opportunity(
        seq=1,
        sender="did:key:z6MkExample",
        offer_id="0xabc",
        amount="200",
        asset="FLOP",
        rails=("paper",),
        job_proto="blockrewards",
        job_context="/kv/job/example",
        expires_ms=None,
    )

    result = evaluate_opportunity(opportunity)

    assert result["eligible"] is True
    assert result["reason"] == "supported_blockrewards_job"

def test_discover_and_evaluate():
    from pui.opportunity import discover_and_evaluate

    def fake_read_room(room, limit=50):
        return {
            "messages": [
                {
                    "seq": 20,
                    "from": "did:key:z6MkAgent",
                    "text": (
                        'tclk1 '
                        '{"amount":"200","asset":"FLOP","id":"0x999",'
                        '"job":{"context":"/kv/job/999","proto":"blockrewards"},'
                        '"rails":["paper"],"type":"offer"}'
                    ),
                }
            ]
        }

    result = discover_and_evaluate(fake_read_room)

    assert result["status"] == "candidate"
    assert result["opportunity"].offer_id == "0x999"
    assert result["decision"]["eligible"] is True

def test_opportunity_snapshot():
    from pui.opportunity import opportunity_snapshot

    def fake_read_room(room, limit=50):
        return {
            "messages": [
                {
                    "seq": 30,
                    "from": "did:key:z6MkAgent",
                    "text": (
                        'tclk1 '
                        '{"amount":"400","asset":"FLOP","id":"0x777",'
                        '"job":{"context":"/kv/job/777","proto":"blockrewards"},'
                        '"rails":["paper"],"type":"offer"}'
                    ),
                }
            ]
        }

    snapshot = opportunity_snapshot(fake_read_room)

    assert snapshot["status"] == "candidate"
    assert snapshot["opportunity"]["seq"] == 30
    assert snapshot["opportunity"]["offer_id"] == "0x777"
    assert snapshot["decision"]["eligible"] is True

def test_discover_latest_eligible_opportunity_skips_unsupported():
    from pui.opportunity import discover_latest_eligible_opportunity

    def fake_read_room(room, limit=200):
        return {
            "messages": [
                {
                    "seq": 10,
                    "from": "did:key:z6MkOld",
                    "text": (
                        'tclk1 '
                        '{"amount":"200","asset":"FLOP","id":"0xold",'
                        '"job":{"context":"/kv/job/old","proto":"blockrewards"},'
                        '"rails":["paper"],"type":"offer"}'
                    ),
                },
                {
                    "seq": 11,
                    "from": "did:key:z6MkNew",
                    "text": (
                        'tclk1 '
                        '{"amount":"200","asset":"PAPER","id":"0xnew",'
                        '"job":{"context":"/kv/job/new","proto":"a2a"},'
                        '"rails":["paper"],"type":"offer"}'
                    ),
                },
            ]
        }

    opportunity = discover_latest_eligible_opportunity(fake_read_room)

    assert opportunity is not None
    assert opportunity.seq == 10
    assert opportunity.offer_id == "0xold"
    assert opportunity.job_proto == "blockrewards"


def test_evaluate_job_context():
    from pui.opportunity import evaluate_job_context

    census = evaluate_job_context(
        "census | source /kv/tclk-mat-67/example"
    )
    assert census["eligible"] is True
    assert census["job_type"] == "census"

    fold = evaluate_job_context(
        "protocol | Fold this tclk/1 transcript with foldTranscript"
    )
    assert fold["eligible"] is False
    assert fold["job_type"] == "protocol_fold"
    assert fold["reason"] == "recognized_but_not_implemented"


def test_discover_latest_executable_opportunity_skips_unimplemented():
    from pui.opportunity import discover_latest_executable_opportunity

    def fake_read_room(room, limit=200):
        assert room == "tclk-offers"

        return {
            "messages": [
                {
                    "seq": 100,
                    "from": "did:key:z6MkCensus",
                    "text": (
                        'tclk1 '
                        '{"amount":"200","asset":"FLOP","id":"0xcensus",'
                        '"job":{"context":"/kv/job/census","proto":"blockrewards"},'
                        '"rails":["paper"],"type":"offer"}'
                    ),
                },
                {
                    "seq": 101,
                    "from": "did:key:z6MkFold",
                    "text": (
                        'tclk1 '
                        '{"amount":"400","asset":"FLOP","id":"0xfold",'
                        '"job":{"context":"/kv/job/fold","proto":"blockrewards"},'
                        '"rails":["paper"],"type":"offer"}'
                    ),
                },
            ]
        }

    def fake_get_text(path):
        if path == "/kv/job/census":
            return "census | source /kv/tclk-mat-67/example"

        if path == "/kv/job/fold":
            return (
                "protocol | Fold this tclk/1 transcript "
                "with foldTranscript"
            )

        raise AssertionError(f"unexpected path: {path}")

    result = discover_latest_executable_opportunity(
        fake_read_room,
        fake_get_text,
    )

    assert result["status"] == "executable"
    assert result["opportunity"].seq == 100
    assert result["opportunity"].offer_id == "0xcensus"
    assert result["decision"]["eligible"] is True
    assert result["decision"]["job_type"] == "census"


def test_evaluate_math_job_context():
    from pui.opportunity import evaluate_job_context

    result = evaluate_job_context(
        "math | [difficulty 1/3] "
        "Compute gcd(10, 20) and lcm(10, 20)."
    )

    assert result["eligible"] is True
    assert result["job_type"] == "math"
    assert result["reason"] == "supported_blockrewards_math"


def test_evaluate_unsupported_math_job_context():
    from pui.opportunity import evaluate_job_context

    result = evaluate_job_context(
        "math | Compute the square root of 144."
    )

    assert result["eligible"] is False
    assert result["job_type"] == "math"
    assert result["reason"] == "unsupported_math_task"


def test_evaluate_opportunity_rejects_expired_offer():
    from pui.opportunity import Opportunity, evaluate_opportunity

    opportunity = Opportunity(
        seq=1,
        sender="did:key:z6MkExample",
        offer_id="0xexpired",
        amount="200",
        asset="FLOP",
        rails=("paper",),
        job_proto="blockrewards",
        job_context="/kv/job/example",
        expires_ms=1_000,
    )

    result = evaluate_opportunity(
        opportunity,
        now_ms=2_000,
    )

    assert result["eligible"] is False
    assert result["reason"] == "expired_offer"


def test_evaluate_opportunity_accepts_unexpired_offer():
    from pui.opportunity import Opportunity, evaluate_opportunity

    opportunity = Opportunity(
        seq=1,
        sender="did:key:z6MkExample",
        offer_id="0xfresh",
        amount="200",
        asset="FLOP",
        rails=("paper",),
        job_proto="blockrewards",
        job_context="/kv/job/example",
        expires_ms=3_000,
    )

    result = evaluate_opportunity(
        opportunity,
        now_ms=2_000,
    )

    assert result["eligible"] is True
    assert result["reason"] == "supported_blockrewards_job"


def test_evaluate_verification_lock_count_job_context():
    from pui.opportunity import evaluate_job_context

    result = evaluate_job_context(
        "verification | From the note /kv/tclk-mat-d4/example "
        "how many rows are lock frames posted by "
        "did:key:z6MkTarget? Give the count."
    )

    assert result["eligible"] is True
    assert result["job_type"] == "verification_lock_count"
    assert result["reason"] == "supported_verification_lock_count"


def test_evaluate_unsupported_verification_job_context():
    from pui.opportunity import evaluate_job_context

    result = evaluate_job_context(
        "verification | Compare two unrelated protocol claims."
    )

    assert result["eligible"] is False
    assert result["job_type"] == "verification"
    assert result["reason"] == "unsupported_verification_task"
