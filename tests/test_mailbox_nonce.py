from pui.mailbox import has_signed_shape, valid_nonce_shape


def test_large_nonce_is_preserved_as_exact_decimal():
    nonce = "900719925474099312345678901"
    assert valid_nonce_shape(nonce)
    assert has_signed_shape({"from": "did:key:z6MkExample", "sig": "abc", "nonce": nonce})


def test_nonce_rejects_lossy_or_ambiguous_values():
    for value in (None, True, False, 1.0, 1.5, -1, "-1", "+1", "1e3", " 1", "", "١٢٣", "1.0"):
        assert not valid_nonce_shape(value), repr(value)
        assert not has_signed_shape({"from": "did:key:z6MkExample", "sig": "abc", "nonce": value})


def test_integer_and_decimal_string_nonce_accepted():
    for value in (0, 123, 2**80, "0", "123", str(2**80)):
        assert valid_nonce_shape(value)
