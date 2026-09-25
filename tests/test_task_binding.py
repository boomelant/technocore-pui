import hashlib
from pui.task_binding import binding_status


def test_reader_pinned_match():
    d = hashlib.sha256(b"spec").hexdigest()
    c = hashlib.sha256(b"checker").hexdigest()
    args = dict(expected_job="j1", actual_job="j1", expected_spec_sha256=d,
                spec_bytes=b"spec", expected_checker_sha256=c, checker_bytes=b"checker")
    assert binding_status(**args) == "MATCH"
    assert binding_status(**{**args, "spec_bytes": b"changed"}) == "MISMATCH"
    assert binding_status(**{**args, "checker_bytes": None}) == "UNKNOWN"
    assert binding_status(**{**args, "actual_job": "j2"}) == "MISMATCH"


def test_known_mismatch_precedes_unknown():
    d = hashlib.sha256(b"spec").hexdigest()
    c = hashlib.sha256(b"checker").hexdigest()
    assert binding_status(expected_job="j1", actual_job="j1", expected_spec_sha256=d,
                          spec_bytes=None, expected_checker_sha256=c,
                          checker_bytes=b"wrong") == "MISMATCH"
