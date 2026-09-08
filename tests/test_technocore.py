from pui.technocore import clean_room_text


def test_clean_room_text_replaces_line_breaks_and_invisibles():
    raw = "hello\nworld\u2028next\u2029done"
    assert clean_room_text(raw) == "hello world next done"


def test_clean_room_text_trims_edges():
    raw = "\n  hello world  \n"
    assert clean_room_text(raw) == "hello world"


def test_send_signed_message_posts_cleaned_text_and_string_nonce(monkeypatch):
    import json
    import pui.technocore as technocore

    captured = {}

    monkeypatch.setattr(
        technocore,
        "sign_room_message",
        lambda room, text: (123456, "test-signature"),
    )
    monkeypatch.setattr(
        technocore,
        "public_did",
        lambda: "did:key:test",
    )

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"ok"

    def fake_urlopen(req, timeout=20):
        captured["request"] = req
        return FakeResponse()

    monkeypatch.setattr(technocore.urllib.request, "urlopen", fake_urlopen)

    result = technocore.send_signed_message(
        "flop_labs",
        "hello\nworld",
    )

    payload = json.loads(captured["request"].data.decode("utf-8"))

    assert result == "ok"
    assert captured["request"].method == "POST"
    assert payload["did"] == "did:key:test"
    assert payload["sig"] == "test-signature"
    assert payload["nonce"] == "123456"
    assert payload["text"] == "hello world"
