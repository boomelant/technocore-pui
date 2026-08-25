import json
from datetime import datetime, timezone

from .config import DATA_DIR


def save_snapshot(room_messages: dict) -> str:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = DATA_DIR / f"snapshot-{stamp}.json"

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "rooms": room_messages,
    }

    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return str(path)
