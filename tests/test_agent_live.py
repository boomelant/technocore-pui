from pui.opportunity import Opportunity


def test_execute_opportunity_once_returns_none_when_no_candidate(monkeypatch):
    import pui.agent_live as agent_live

    monkeypatch.setattr(
        agent_live,
        "discover_latest_executable_opportunity",
        lambda read_room, get_text: {
            "status": "none",
            "opportunity": None,
            "decision": None,
            "job_context_text": None,
        },
    )

    result = agent_live.execute_opportunity_once()

    assert result["status"] == "none"
    assert result["executed"] is False


def test_execute_opportunity_once_processes_executable_candidate(monkeypatch):
    import pui.agent_live as agent_live

    opportunity = Opportunity(
        seq=700,
        sender="did:key:z6MkExample",
        offer_id="0xagent-live",
        amount="200",
        asset="FLOP",
        rails=("paper",),
        job_proto="blockrewards",
        job_context="/kv/tclk-job/example",
        expires_ms=None,
    )

    monkeypatch.setattr(
        agent_live,
        "discover_latest_executable_opportunity",
        lambda read_room, get_text: {
            "status": "executable",
            "opportunity": opportunity,
            "decision": {
                "eligible": True,
                "job_type": "math",
            },
            "job_context_text": (
                "math | Compute gcd(10, 20) and lcm(10, 20)."
            ),
        },
    )

    monkeypatch.setattr(
        agent_live,
        "process_opportunity",
        lambda opportunity, get_text: {
            "task_id": "tclk:0xagent-live",
            "status": "completed",
            "verified": True,
            "written": True,
            "result_hash": "sha256:test",
        },
    )

    result = agent_live.execute_opportunity_once()

    assert result["status"] == "completed"
    assert result["executed"] is True
    assert result["verified"] is True
    assert result["written"] is True
    assert result["offer_id"] == "0xagent-live"


def test_opportunity_cycle_once_combines_snapshot_and_execution(monkeypatch):
    import pui.agent_live as agent_live

    monkeypatch.setattr(
        agent_live,
        "scan_opportunity_once",
        lambda: {
            "status": "candidate",
            "decision": {
                "eligible": True,
            },
        },
    )

    monkeypatch.setattr(
        agent_live,
        "execute_opportunity_once",
        lambda: {
            "status": "completed",
            "executed": True,
            "verified": True,
            "written": True,
            "offer_id": "0xcycle",
        },
    )

    result = agent_live.opportunity_cycle_once()

    assert result["snapshot"]["status"] == "candidate"
    assert result["execution"]["status"] == "completed"
    assert result["execution"]["executed"] is True
    assert result["execution"]["offer_id"] == "0xcycle"
