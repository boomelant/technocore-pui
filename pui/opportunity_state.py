import json
from datetime import datetime, timezone
from pathlib import Path

STATE_PATH = Path("data/opportunity-state.json")


def write_opportunity_state(result: dict) -> None:
    payload = {
        "protocol": "PUI-OPPORTUNITY-STATE/1",
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
