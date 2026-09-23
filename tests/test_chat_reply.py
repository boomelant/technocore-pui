import pytest

import pui.chat_reply as chat

SOURCE = {"seq": 7, "from": "did:key:z6MkPeer", "sig": "source-sig", "text": "Can you audit this?"}
SELF = "did:key:z6MkPui"


@pytest.fixture(autouse=True)
def identity(monkeypatch):
    monkeypatch.setattr(chat, "public_did", lambda: SELF)
    monkeypatch.setattr(chat, "sign_room_message", lambda room, text: (12345, "our-sig"))


def read_from(messages):
    def read(room, limit=200):
        assert room == "technocore"
        return {"messages": messages}
    return read


def test_draft_binds_existing_signed_source_and_does_not_send():
    draft = chat.prepare_reply("technocore", 7, "I can verify the fixture.", read=read_from([SOURCE]))
    assert draft["source_sender"] == SOURCE["from"]
    assert draft["status"] == "ready_for_review"
    assert "Re 7 (did:key:z6MkPeer)" in draft["text"]


@pytest.mark.parametrize("source", [
    {"seq": 7, "from": "anonymous", "sig": "sig"},
    {"seq": 7, "from": "did:key:z6MkPeer"},
    {"seq": 7, "from": SELF, "sig": "sig"},
])
def test_reject_unsafe_source(source):
    with pytest.raises(ValueError):
        chat.prepare_reply("technocore", 7, "hello", read=read_from([source]))


def test_reject_missing_source_and_invalid_room():
    with pytest.raises(ValueError, match="not found"):
        chat.prepare_reply("technocore", 7, "hello", read=read_from([]))
    with pytest.raises(ValueError, match="invalid"):
        chat.prepare_reply("../private", 7, "hello", read=read_from([SOURCE]))


def test_no_send_without_explicit_approval():
    draft = chat.prepare_reply("technocore", 7, "I checked the issue.", read=read_from([SOURCE]))
    with pytest.raises(PermissionError):
        chat.send_reviewed_reply(draft, post=lambda *args: pytest.fail("posted"))


def test_send_requires_exact_readback_evidence():
    messages = [SOURCE.copy()]
    draft = chat.prepare_reply("technocore", 7, "I checked the issue.", read=read_from(messages))

    def post(url, payload):
        assert url.endswith("/r/technocore")
        assert payload["did"] == SELF
        assert payload["nonce"] == "12345"
        assert payload["sig"] == "our-sig"
        messages.append({**payload, "from": SELF, "seq": 8})

    receipt = chat.send_reviewed_reply(draft, approved=True, read=read_from(messages), post=post)
    assert receipt["status"] == "confirmed"
    assert receipt["seq"] == 8
    # Retry must not post the same reply again.
    repeated = chat.send_reviewed_reply(
        draft, approved=True, read=read_from(messages),
        post=lambda *args: pytest.fail("duplicate"),
    )
    assert repeated["status"] == "already_posted"


def test_missing_readback_does_not_claim_publication():
    messages = [SOURCE.copy()]
    draft = chat.prepare_reply("technocore", 7, "One useful answer.", read=read_from(messages))
    result = chat.send_reviewed_reply(draft, approved=True, read=read_from(messages),
                                      post=lambda *args: None)
    assert result["status"] == "unconfirmed"


def test_draft_rejected_when_source_identity_changes():
    messages = [SOURCE.copy()]
    draft = chat.prepare_reply("technocore", 7, "One useful answer.", read=read_from(messages))
    messages[0]["from"] = "did:key:z6MkAnother"
    with pytest.raises(ValueError, match="mismatch"):
        chat.send_reviewed_reply(draft, approved=True, read=read_from(messages),
                                 post=lambda *args: pytest.fail("posted"))
