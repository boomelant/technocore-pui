import json
from pathlib import Path


STATE_PATH = Path("data/agent-state.json")


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"rooms": {}}

    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"rooms": {}}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def get_last_processed(room: str) -> int | None:
    state = load_state()
    room_state = state.get("rooms", {}).get(room, {})
    return room_state.get("last_processed_seq")


def set_last_processed(room: str, seq: int) -> None:
    state = load_state()

    rooms = state.setdefault("rooms", {})
    room_state = rooms.setdefault(room, {})

    room_state["last_processed_seq"] = seq

    save_state(state)
