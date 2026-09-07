import json

from pui import chronicle_status


def test_build_status_includes_task_runner_state(tmp_path, monkeypatch):
    state_path = tmp_path / "task-runner-state.json"

    state_path.write_text(
        json.dumps(
            {
                "updated_at": "2026-09-07T09:00:00+00:00",
                "result": {
                    "task_id": "queue:lobby:5000",
                    "status": "completed",
                    "verified": True,
                    "written": True,
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        chronicle_status,
        "TASK_RUNNER_STATE",
        state_path,
    )

    monkeypatch.setattr(
        chronicle_status,
        "top_cross_room_dids",
        lambda limit=10: [],
    )

    monkeypatch.setattr(
        chronicle_status,
        "room_status",
        lambda room: {"room": room, "status": "test"},
    )

    status = chronicle_status.build_status()

    runner = status["task_runner"]

    assert runner["status"] == "online"
    assert runner["updated_at"] == "2026-09-07T09:00:00+00:00"
    assert runner["result"]["task_id"] == "queue:lobby:5000"
    assert runner["result"]["verified"] is True
