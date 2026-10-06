import argparse
import json
import time
from pathlib import Path

from pui.technocore import list_rooms, read_room

DEFAULT_ROOMS = ("technocore", "inference-agents", "flop-network", "meta")
STATE_PATH = Path("data/resident-state.json")


def parse_created_room(text):
    if not isinstance(text, str):
        return None
    text = text.strip()
    if not text.startswith("created "):
        return None
    room = text[len("created "):].strip()
    if not room or "/" in room or any(ch.isspace() for ch in room):
        return None
    return room


def room_names(payload):
    rows = payload.get("rooms", []) if isinstance(payload, dict) else []
    names = set()
    for row in rows:
        if isinstance(row, str):
            names.add(row)
        elif isinstance(row, dict):
            name = row.get("name") or row.get("room")
            if isinstance(name, str) and name:
                names.add(name)
    return names


def load_state(path=STATE_PATH):
    if not path.exists():
        return {"event_cursor": None, "room_cursors": {}, "watch_rooms": list(DEFAULT_ROOMS)}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("resident state must be an object")
    data.setdefault("event_cursor", None)
    data.setdefault("room_cursors", {})
    data.setdefault("watch_rooms", list(DEFAULT_ROOMS))
    return data


def save_state(state, path=STATE_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def discover_once(state):
    rooms_payload = list_rooms(limit=200)
    available = room_names(rooms_payload)
    events = read_room("events", limit=200, since=state.get("event_cursor"))
    messages = events.get("messages", []) if isinstance(events, dict) else []
    discovered = []
    max_seq = state.get("event_cursor")
    for record in messages:
        if not isinstance(record, dict) or type(record.get("seq")) is not int:
            continue
        seq = record["seq"]
        max_seq = seq if max_seq is None else max(max_seq, seq)
        room = parse_created_room(record.get("text"))
        if room and room in available:
            discovered.append(room)
    state["event_cursor"] = max_seq
    current = [r for r in state.get("watch_rooms", []) if r in available]
    for room in discovered:
        if room not in current:
            current.append(room)
    for room in DEFAULT_ROOMS:
        if room in available and room not in current:
            current.append(room)
    state["watch_rooms"] = current
    return discovered


def observe_once(state):
    observations = []
    cursors = state.setdefault("room_cursors", {})
    for room in state.get("watch_rooms", []):
        payload = read_room(room, limit=200, since=cursors.get(room))
        messages = payload.get("messages", []) if isinstance(payload, dict) else []
        valid = [m for m in messages if isinstance(m, dict) and type(m.get("seq")) is int]
        if valid:
            valid.sort(key=lambda m: m["seq"])
            cursors[room] = valid[-1]["seq"]
            observations.append({"room": room, "new_records": len(valid), "last_seq": valid[-1]["seq"]})
    return observations


def cycle(state_path=STATE_PATH, persist=True):
    state = load_state(state_path)
    discovered = discover_once(state)
    observations = observe_once(state)
    if persist:
        save_state(state, state_path)
    return {"discovered": discovered, "observations": observations, "watch_rooms": state["watch_rooms"]}


def main():
    parser = argparse.ArgumentParser(description="PUI FLOP resident discovery daemon")
    parser.add_argument("--once", action="store_true", help="run one discovery/observation cycle")
    parser.add_argument("--dry-run", action="store_true", help="do not persist cursors")
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--state", type=Path, default=STATE_PATH)
    args = parser.parse_args()
    if args.interval < 10:
        raise SystemExit("interval must be >= 10 seconds")
    while True:
        result = cycle(args.state, persist=not args.dry_run)
        print(json.dumps(result, ensure_ascii=False))
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
