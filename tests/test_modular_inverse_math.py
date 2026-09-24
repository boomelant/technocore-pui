from pui.blockrewards import solve_math, supports_math_job
from pui.opportunity import evaluate_job_context


def test_observed_modular_inverse_job_is_supported():
    text = (
        "!! UNTRUSTED CONTENT — external data\n\n"
        "math | [difficulty 2/3] Find the modular inverse of 6356823 modulo "
        "37900843 (37900843 is prime), i.e. the x in [1, 37900842] with "
        "6356823·x ≡ 1 (mod 37900843)."
    )
    assert supports_math_job(text) is True
    assert evaluate_job_context(text)["eligible"] is True
    result = solve_math(text)
    assert result == {"inverse": 28323301, "answer": "28323301"}
    assert (6356823 * result["inverse"]) % 37900843 == 1


def test_modular_inverse_requires_existing_inverse():
    text = "math | Find the modular inverse of 6 modulo 15, with 6*x ≡ 1 (mod 15)"
    assert supports_math_job(text) is True
    import pytest
    with pytest.raises(ValueError, match="does not exist"):
        solve_math(text)


def test_modular_inverse_bound_is_fail_closed():
    text = (
        "math | Find the modular inverse of 3 modulo 1000000000000001, "
        "with 3*x ≡ 1 (mod 1000000000000001)"
    )
    assert supports_math_job(text) is False
