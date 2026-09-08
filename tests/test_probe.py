from pui.probe import parse_probe, collect_response_candidates


def test_parse_real_probe_v1():
    message = {
        "seq": 1987600,
        "from": "did:key:test",
        "ts": "2026-09-08T11:48:54.837732Z",
        "text": (
            "probe v1 | 0909a-meta.124 | null | "
            "This line is a measurement and expects no reply. "
            "It stands here so that silence has a baseline."
        ),
    }

    result = parse_probe("meta", message)

    assert result is not None
    assert result["room"] == "meta"
    assert result["seq"] == 1987600
    assert result["probe_id"] == "0909a-meta.124"
    assert result["condition"] == "null"
    assert result["sender"] == "did:key:test"


def test_ignore_non_probe():
    message = {
        "seq": 101,
        "from": "did:key:test",
        "ts": "2026-09-08T10:00:01Z",
        "text": "Peer probe: verifying state proofs",
    }

    assert parse_probe("technocore", message) is None


def test_collect_response_candidates_within_120_seconds():
    probe = {
        "room": "technocore",
        "seq": 100,
        "probe_id": "test.1",
        "condition": "question",
        "sender": "did:key:probe",
        "ts": "2026-09-08T10:00:00Z",
        "text": "probe v1 | test.1 | question | test",
    }

    messages = [
        {
            "seq": 101,
            "from": "did:key:probe",
            "ts": "2026-09-08T10:00:05Z",
            "text": "self message",
        },
        {
            "seq": 102,
            "from": "did:key:a",
            "ts": "2026-09-08T10:00:20Z",
            "text": "candidate one",
        },
        {
            "seq": 103,
            "from": "did:key:b",
            "ts": "2026-09-08T10:01:30Z",
            "text": "candidate two",
        },
        {
            "seq": 104,
            "from": "did:key:c",
            "ts": "2026-09-08T10:02:01Z",
            "text": "too late",
        },
    ]

    result = collect_response_candidates(probe, messages)

    assert result["candidate_response_count"] == 2
    assert result["unique_responders"] == 2
    assert result["first_response_latency_ms"] == 20000
    assert [x["seq"] for x in result["responses"]] == [102, 103]


from pui.probe import is_explicit_probe_response


def test_explicit_ask_response_requires_probe_id():
    probe = {
        "probe_id": "0909a-technocore.1",
        "condition": "ask",
        "sender": "did:key:probe",
    }

    matching = {
        "from": "did:key:agent",
        "text": (
            "For 0909a-technocore.1 I would choose tclk-offers "
            "because it exposes real agent work."
        ),
    }

    unrelated = {
        "from": "did:key:agent2",
        "text": "I would choose tclk-offers.",
    }

    self_reply = {
        "from": "did:key:probe",
        "text": "0909a-technocore.1",
    }

    assert is_explicit_probe_response(probe, matching) is True
    assert is_explicit_probe_response(probe, unrelated) is False
    assert is_explicit_probe_response(probe, self_reply) is False


def test_null_probe_never_has_explicit_response():
    probe = {
        "probe_id": "0909a-meta.124",
        "condition": "null",
        "sender": "did:key:probe",
    }

    message = {
        "from": "did:key:agent",
        "text": "0909a-meta.124",
    }

    assert is_explicit_probe_response(probe, message) is False
