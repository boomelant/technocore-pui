import json

from pui import task_runner_state


def test_write_runner_state(tmp_path):
    task_runner_state.STATE_PATH = tmp_path / "task-runner-state.json"

    result = {
        "task_id": "queue:lobby:4000",
        "status": "completed",
        "verified": True,
        "written": True,
    }

    task_runner_state.write_runner_state(result)

    data = json.loads(
        task_runner_state.STATE_PATH.read_text(encoding="utf-8")
    )

    assert data["result"] == result
    assert isinstance(data["updated_at"], str)
    assert data["updated_at"]
