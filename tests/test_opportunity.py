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
