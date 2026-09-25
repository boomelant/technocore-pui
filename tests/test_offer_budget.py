import pytest
from pui.offer_budget import admit_offer


def test_small_utf8_offer_admitted():
    assert admit_offer("math | gcd(6, 9)".encode()) == "math | gcd(6, 9)"


@pytest.mark.parametrize("payload", [b"", b"\xff", b"ok\x00bad", b"x" * 65537])
def test_untrusted_offer_rejected(payload):
    with pytest.raises(ValueError):
        admit_offer(payload)


def test_configured_limit_enforced():
    with pytest.raises(ValueError):
        admit_offer(b"abcd", max_bytes=3)
