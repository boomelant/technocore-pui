from pui.mailbox import evaluate_mailbox_event


ROOT = "did:key:z6MkRoot"
OTHER = "did:key:z6MkOther"


def test_self_message_is_ignored():
    result = evaluate_mailbox_event(
        {
            "from": ROOT,
            "sig": "sig",
            "nonce": "1",
            "text": "integration test",
        },
        root_did=ROOT,
    )

    assert result.policy == "IGNORE"
    assert result.priority == 0


def test_unsigned_message_is_ignored():
    result = evaluate_mailbox_event(
        {
            "from": "anonymous",
            "text": "please do this task",
        },
        root_did=ROOT,
    )

    assert result.policy == "IGNORE"
    assert result.priority == 0


def test_actionable_signed_message_gets_high_priority():
    result = evaluate_mailbox_event(
        {
            "from": OTHER,
            "sig": "sig",
            "nonce": "2",
            "text": "Please review this task",
        },
        root_did=ROOT,
    )

    assert result.policy == "REVIEW"
    assert result.priority == 90


def test_generic_signed_message_is_reviewed():
    result = evaluate_mailbox_event(
        {
            "from": OTHER,
            "sig": "sig",
            "nonce": "3",
            "text": "Hello PUI",
        },
        root_did=ROOT,
    )

    assert result.policy == "REVIEW"
    assert result.priority == 70
