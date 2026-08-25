from pui.scoring import analyze_messages


def msg(author, text):
    return {
        "from": author,
        "text": text,
        "signed": True,
    }


def test_organic_activity_scores_lower_coordination():
    messages = [
        msg("did:key:a1", "Discussing relay timeout handling"),
        msg("did:key:a2", "Testing room pagination behavior"),
        msg("did:key:a3", "Reviewing signed write semantics"),
        msg("did:key:a4", "Checking DID namespace limits"),
        msg("did:key:a5", "Comparing retry strategies"),
        msg("did:key:a6", "Documenting verifier behavior"),
        msg("did:key:a7", "Investigating cross room activity"),
        msg("did:key:a8", "Testing local report generation"),
    ]

    result = analyze_messages(messages)

    assert result["coordination_risk"] < 50


def test_repeated_one_shot_campaign_scores_higher():
    messages = [
        msg(f"did:key:campaign{i}", "Agent node alive. Meta participation logged.")
        for i in range(20)
    ]

    result = analyze_messages(messages)

    assert result["coordination_risk"] > 70
    assert result["repetition_ratio"] > 0.9
    assert result["one_shot_ratio"] > 0.9


def test_single_active_author_is_not_one_shot_campaign():
    messages = [
        msg("did:key:worker", f"Useful analysis result number {i}")
        for i in range(10)
    ]

    result = analyze_messages(messages)

    assert result["one_shot_ratio"] == 0.0


def test_near_duplicate_campaign_is_not_treated_as_fully_organic():
    messages = [
        msg(f"did:key:variant{i}", f"Agent node alive. Meta participation logged. Variant {i}")
        for i in range(20)
    ]

    result = analyze_messages(messages)

    assert result["coordination_risk"] > 40
