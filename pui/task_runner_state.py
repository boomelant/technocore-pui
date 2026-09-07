import json
from datetime import datetime, timezone
from pathlib import Path


STATE_PATH = Path("data/task-runner-state.json")


def write_runner_state(result: dict) -> None:
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "result": result,
    }

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
