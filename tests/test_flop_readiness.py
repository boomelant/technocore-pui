from pui.flop_readiness import detect_signals


def test_detects_explicit_faucet_endpoint():
    text = "Official faucet URL: https://testnet.example/faucet"
    result = detect_signals(text)

    assert result["faucet_evidence"]


def test_planned_faucet_text_is_not_endpoint():
    text = "Agents will claim a test-token faucet during testnet."
    result = detect_signals(text)

    assert result["faucet_evidence"] == []
