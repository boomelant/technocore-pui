import pytest
from pui.raw_artifact import describe_artifact, verify_artifact


def test_exact_raw_bytes_match():
    raw = b'{"a":1,"b":2}\n'
    assert verify_artifact(raw, **describe_artifact(raw))


def test_json_reserialization_does_not_preserve_digest():
    original = b'{"a":1,"b":2}\n'
    reformatted = b'{ "b": 2, "a": 1 }\n'
    assert not verify_artifact(reformatted, **describe_artifact(original))


def test_size_mismatch_fails():
    raw = b"abc"
    descriptor = describe_artifact(raw)
    assert not verify_artifact(raw, sha256=descriptor["sha256"], size=4)


def test_text_and_unbounded_bytes_rejected():
    with pytest.raises(ValueError):
        describe_artifact("abc")
    with pytest.raises(ValueError):
        describe_artifact(b"x" * (16 * 1024 * 1024 + 1))
