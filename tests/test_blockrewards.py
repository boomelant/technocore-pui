from pui.blockrewards import solve_census


def test_solve_census():
    material = """
seq | id | payer | amount | asset | rails | proto | role
1 | 0xaaa | Alice | 200 | FLOP | paper | blockrewards | payer
2 | 0xbbb | Bob | 400 | FLOP | paper | blockrewards | payer
3 | 0xccc | Alice | 800 | FLOP | paper | blockrewards | payer
4 | 0xddd | Carol | 100 | PAPER | paper | pin | payer
5 | 0xeee | Bob | 10 | FLOP | paper | acp | payee
"""

    result = solve_census(material)

    assert result["offers"] == 5
    assert result["payers"] == 3
    assert result["top_payer"] == "Alice"
    assert result["top_count"] == 2
    assert result["answer"] == "offers=5; payers=3; top=Alice:2"


def test_extract_material_path():
    from pui.blockrewards import extract_material_path

    context = (
        "census | [difficulty 1/3] From the note "
        "/kv/tclk-mat-67/mcensus-80499c "
        "(an excerpt of the board)"
    )

    assert (
        extract_material_path(context)
        == "/kv/tclk-mat-67/mcensus-80499c"
    )


def test_classify_job_context():
    from pui.blockrewards import classify_job_context

    assert (
        classify_job_context(
            "census | From the note /kv/tclk-mat-67/example"
        )
        == "census"
    )

    assert (
        classify_job_context(
            "protocol | Fold this tclk/1 transcript with the reference rules (foldTranscript)"
        )
        == "protocol_fold"
    )

    assert classify_job_context("something else") == "unsupported"


def test_classify_math_and_validation():
    from pui.blockrewards import classify_job_context

    assert (
        classify_job_context(
            "math | [difficulty 1/3] Compute gcd(10, 20) and lcm(10, 20)."
        )
        == "math"
    )

    assert (
        classify_job_context(
            "validation | Validate a deliverable. TASK that was posted: example"
        )
        == "validation"
    )


def test_solve_math_gcd_lcm():
    from pui.blockrewards import solve_math

    result = solve_math(
        "math | [difficulty 1/3] "
        "Compute gcd(755555505455, 336499273165399) "
        "and lcm(755555505455, 336499273165399)."
    )

    assert result["gcd"] > 0
    assert result["lcm"] > 0
    assert result["answer"].startswith("gcd=")
    assert " lcm=" in result["answer"]


def test_supports_math_job():
    from pui.blockrewards import supports_math_job

    assert supports_math_job(
        "math | Compute gcd(10, 20) and lcm(10, 20)."
    ) is True

    assert supports_math_job(
        "math | Compute the square root of 144."
    ) is False


def test_extract_tclk_transcript():
    from pui.blockrewards import extract_tclk_transcript

    context = (
        'protocol | material: '
        'tclk-offers | 2026-09-07T14:52:07.555Z | '
        'did:key:z6MkuNUQk6RNdzLMBXRrjZb21z8qwkvttHr4X88bgmMzb4FV | '
        'tclk1 {"amount":"2870","type":"offer"} '
        'tclk-offers | 2026-09-07T14:52:27.555Z | '
        'did:key:z6MkvXUEP6Qn45pAGkBuPJ444W6Ek9DyfhNVjq9RBkNVibfR | '
        'tclk1 {"contract":"0xabc","type":"accept"} '
        'mb-p-tclk-ed297e603c79d982 | 2026-09-07T14:52:47.555Z | '
        'did:key:z6Mki3ty6nDBkqB8TwTvNoaJ85qoHvMtVvuiz9WVB4r96Bb2 | '
        'tclk1 {"contract":"0xabc","type":"lock"}'
    )

    records = extract_tclk_transcript(context)

    assert len(records) == 3
    assert records[0]["room"] == "tclk-offers"
    assert '"type":"offer"' in records[0]["frame"]
    assert '"type":"accept"' in records[1]["frame"]
    assert records[2]["room"] == "mb-p-tclk-ed297e603c79d982"
    assert '"type":"lock"' in records[2]["frame"]


def test_parse_tclk_transcript():
    from pui.blockrewards import parse_tclk_transcript

    context = (
        'protocol | material: '
        'tclk-offers | 2026-09-07T14:52:07.555Z | '
        'did:key:z6MkPayer | '
        'tclk1 {"id":"0xoffer","type":"offer"} '
        'tclk-offers | 2026-09-07T14:52:27.555Z | '
        'did:key:z6MkWorker | '
        'tclk1 {"contract":"0xa84a62c2f7937e3e000000000000000000000000000000000000000000000000","ref":"0xoffer","type":"accept"}'
    )

    records = parse_tclk_transcript(context)

    assert len(records) == 2
    assert records[0]["type"] == "offer"
    assert records[0]["payload"]["id"] == "0xoffer"
    assert records[1]["type"] == "accept"
    assert records[1]["payload"]["contract"] == "0xa84a62c2f7937e3e000000000000000000000000000000000000000000000000"


def test_fold_tclk_transcript_happy_path():
    from pui.blockrewards import fold_tclk_transcript

    context = (
        'protocol | material: '
        'tclk-offers | 2026-09-07T14:52:07.555Z | '
        'did:key:z6MkPayer | '
        'tclk1 {"id":"0xoffer","type":"offer"} '
        'tclk-offers | 2026-09-07T14:52:27.555Z | '
        'did:key:z6MkWorker | '
        'tclk1 {"contract":"0xa84a62c2f7937e3e000000000000000000000000000000000000000000000000","ref":"0xoffer","type":"accept"} '
        'mb-p-tclk-a84a62c2f7937e3e | 2026-09-07T14:52:47.555Z | '
        'did:key:z6MkPayer | '
        'tclk1 {"contract":"0xa84a62c2f7937e3e000000000000000000000000000000000000000000000000","type":"lock"} '
        'mb-p-tclk-a84a62c2f7937e3e | 2026-09-07T14:53:07.555Z | '
        'did:key:z6MkWorker | '
        'tclk1 {"contract":"0xa84a62c2f7937e3e000000000000000000000000000000000000000000000000","type":"reveal"} '
        'mb-p-tclk-a84a62c2f7937e3e | 2026-09-07T14:53:27.555Z | '
        'did:key:z6MkPayer | '
        'tclk1 {"contract":"0xa84a62c2f7937e3e000000000000000000000000000000000000000000000000","type":"receipt"}'
    )

    result = fold_tclk_transcript(context)

    assert result["status"] == "claimed"
    assert result["rejected"] == []


def test_fold_tclk_transcript_refund_path():
    from pui.blockrewards import fold_tclk_transcript

    context = (
        'protocol | material: '
        'tclk-offers | 2026-09-07T14:52:07.555Z | '
        'did:key:z6MkPayer | '
        'tclk1 {"id":"0xoffer","type":"offer"} '
        'tclk-offers | 2026-09-07T14:52:27.555Z | '
        'did:key:z6MkWorker | '
        'tclk1 {"contract":"0xa84a62c2f7937e3e000000000000000000000000000000000000000000000000","type":"accept"} '
        'mb-p-tclk-a84a62c2f7937e3e | 2026-09-07T14:52:47.555Z | '
        'did:key:z6MkPayer | '
        'tclk1 {"contract":"0xa84a62c2f7937e3e000000000000000000000000000000000000000000000000","type":"lock"} '
        'mb-p-tclk-a84a62c2f7937e3e | 2026-09-07T15:52:47.555Z | '
        'did:key:z6MkPayer | '
        'tclk1 {"contract":"0xa84a62c2f7937e3e000000000000000000000000000000000000000000000000","type":"refund"} '
        'mb-p-tclk-a84a62c2f7937e3e | 2026-09-07T15:53:00.555Z | '
        'did:key:z6MkPayer | '
        'tclk1 {"contract":"0xa84a62c2f7937e3e000000000000000000000000000000000000000000000000","type":"receipt"}'
    )

    result = fold_tclk_transcript(context)

    assert result["status"] == "refunded"
    assert result["rejected"] == []


def test_fold_tclk_transcript_cancel_path():
    from pui.blockrewards import fold_tclk_transcript

    context = (
        'protocol | material: '
        'tclk-offers | 2026-09-07T14:52:07.555Z | '
        'did:key:z6MkPayer | '
        'tclk1 {"id":"0xoffer","type":"offer"} '
        'tclk-offers | 2026-09-07T14:52:27.555Z | '
        'did:key:z6MkPayer | '
        'tclk1 {"type":"cancel"}'
    )

    result = fold_tclk_transcript(context)

    assert result["status"] == "cancelled"
    assert result["rejected"] == []


def test_fold_tclk_transcript_heartbeat_does_not_change_state():
    from pui.blockrewards import fold_tclk_transcript

    context = (
        'protocol | material: '
        'tclk-offers | 2026-09-07T14:52:07.555Z | '
        'did:key:z6MkPayer | '
        'tclk1 {"id":"0xoffer","type":"offer"} '
        'tclk-offers | 2026-09-07T14:52:27.555Z | '
        'did:key:z6MkWorker | '
        'tclk1 {"contract":"0xa84a62c2f7937e3e000000000000000000000000000000000000000000000000","type":"accept"} '
        'mb-p-tclk-a84a62c2f7937e3e | 2026-09-07T14:52:37.555Z | '
        'did:key:z6MkWorker | '
        'tclk1 {"contract":"0xa84a62c2f7937e3e000000000000000000000000000000000000000000000000","type":"heartbeat"} '
        'mb-p-tclk-a84a62c2f7937e3e | 2026-09-07T14:52:47.555Z | '
        'did:key:z6MkPayer | '
        'tclk1 {"contract":"0xa84a62c2f7937e3e000000000000000000000000000000000000000000000000","type":"lock"}'
    )

    result = fold_tclk_transcript(context)

    assert result["status"] == "locked"
    assert result["rejected"] == []


def test_fold_tclk_transcript_rejects_out_of_turn_frame_without_state_change():
    from pui.blockrewards import fold_tclk_transcript

    context = (
        'protocol | material: '
        'tclk-offers | 2026-09-07T14:52:07.555Z | '
        'did:key:z6MkPayer | '
        'tclk1 {"id":"0xoffer","type":"offer"} '
        'tclk-offers | 2026-09-07T14:52:27.555Z | '
        'did:key:z6MkWorker | '
        'tclk1 {"contract":"0xa84a62c2f7937e3e000000000000000000000000000000000000000000000000","type":"accept"} '
        'mb-p-tclk-a84a62c2f7937e3e | 2026-09-07T14:52:37.555Z | '
        'did:key:z6MkWorker | '
        'tclk1 {"contract":"0xa84a62c2f7937e3e000000000000000000000000000000000000000000000000","type":"reveal"} '
        'mb-p-tclk-a84a62c2f7937e3e | 2026-09-07T14:52:47.555Z | '
        'did:key:z6MkPayer | '
        'tclk1 {"contract":"0xa84a62c2f7937e3e000000000000000000000000000000000000000000000000","type":"lock"}'
    )

    result = fold_tclk_transcript(context)

    assert result["status"] == "locked"
    assert len(result["rejected"]) == 1
    assert result["rejected"][0]["type"] == "reveal"
    assert "accepted" in result["rejected"][0]["reason"]


def test_fold_tclk_transcript_rejects_lock_in_wrong_room():
    from pui.blockrewards import fold_tclk_transcript

    contract = (
        "0xa84a62c2f7937e3e"
        "000000000000000000000000000000000000000000000000"
    )

    context = (
        'protocol | material: '
        'tclk-offers | 2026-09-07T14:52:07.555Z | '
        'did:key:z6MkPayer | '
        'tclk1 {"id":"0xoffer","type":"offer"} '
        'tclk-offers | 2026-09-07T14:52:27.555Z | '
        'did:key:z6MkWorker | '
        f'tclk1 {{"contract":"{contract}","type":"accept"}} '
        'mb-p-tclk-deadbeefdeadbeef | 2026-09-07T14:52:47.555Z | '
        'did:key:z6MkPayer | '
        f'tclk1 {{"contract":"{contract}","type":"lock"}}'
    )

    result = fold_tclk_transcript(context)

    assert result["status"] == "accepted"
    assert len(result["rejected"]) == 1
    assert result["rejected"][0]["type"] == "lock"
    assert "mb-p-tclk-a84a62c2f7937e3e" in result["rejected"][0]["reason"]


def test_format_protocol_fold_answer():
    from pui.blockrewards import format_protocol_fold_answer

    assert (
        format_protocol_fold_answer(
            {
                "status": "claimed",
                "rejected": [],
            }
        )
        == "claimed\nno rejected records"
    )

    assert (
        format_protocol_fold_answer(
            {
                "status": "accepted",
                "rejected": [
                    {
                        "type": "lock",
                        "reason": "lock must be posted in mb-p-tclk-example",
                    }
                ],
            }
        )
        == (
            "accepted\n"
            "lock rejected: lock must be posted in mb-p-tclk-example"
        )
    )
