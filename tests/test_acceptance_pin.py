from pui.acceptance_pin import acceptance_matches


def test_matching_authenticated_acceptance():
    args = dict(expected_task="job-1", expected_artifact="a" * 64,
                declared_task="job-1", declared_artifact="a" * 64)
    assert acceptance_matches(**args, signature_verified=True)
    assert not acceptance_matches(**args, signature_verified=False)


def test_cross_task_acceptance_rejected():
    assert not acceptance_matches(expected_task="job-1", declared_task="job-2",
                                  expected_artifact="a" * 64, declared_artifact="a" * 64,
                                  signature_verified=True)


def test_cross_artifact_acceptance_rejected():
    assert not acceptance_matches(expected_task="job-1", declared_task="job-1",
                                  expected_artifact="a" * 64, declared_artifact="b" * 64,
                                  signature_verified=True)
