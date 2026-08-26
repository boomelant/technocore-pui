import json
import time
import threading
from pathlib import Path

from pui.technocore import read_room


DATA_DIR = Path("data/chronicle")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_state(room):
    path = DATA_DIR / f"{room}-state.json"

    if not path.exists():
        return {
            "room": room,
            "last_seq": None,
            "records": 0,
            "gaps": [],
        }

    return json.loads(path.read_text(encoding="utf-8"))


def save_state(room, state):
    path = DATA_DIR / f"{room}-state.json"
    path.write_text(
        json.dumps(state, indent=2),
        encoding="utf-8",
    )


def append_records(room, records):
    path = DATA_DIR / f"{room}.jsonl"

    with path.open("a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def poll_room(room):
    state = load_state(room)

    payload = read_room(room, limit=200, since=state["last_seq"])
    records = payload.get("messages", [])

    if not records:
        print(room, "no records")
        return

    records = sorted(records, key=lambda x: x.get("seq", 0))

    if state["last_seq"] is not None:
        expected = state["last_seq"] + 1
        first_seq = records[0].get("seq")

        if first_seq is not None and first_seq > expected:
            state["gaps"].append({
                "from": expected,
                "to": first_seq - 1,
                "detected_at": int(time.time()),
            })

    new_records = []

    for record in records:
        seq = record.get("seq")

        if seq is None:
            continue

        if state["last_seq"] is None or seq > state["last_seq"]:
            new_records.append(record)

    if new_records:
        append_records(room, new_records)

        state["last_seq"] = new_records[-1]["seq"]
        state["records"] += len(new_records)

        save_state(room, state)

    print(
        room,
        "new:",
        len(new_records),
        "last_seq:",
        state["last_seq"],
        "total:",
        state["records"],
        "gaps:",
        len(state["gaps"]),
    )


def follow_room(room, wait=5):
    print("FOLLOWING:", room)

    while True:
        state = load_state(room)

        payload = read_room(
            room,
            limit=200,
            since=state["last_seq"],
            wait=wait,
        )

        records = payload.get("messages", [])

        if not records:
            print(room, "idle")
            continue

        records = sorted(records, key=lambda x: x.get("seq", 0))

        new_records = []

        for record in records:
            seq = record.get("seq")

            if seq is None:
                continue

            if state["last_seq"] is None or seq > state["last_seq"]:
                new_records.append(record)

        if new_records:
            first_seq = new_records[0]["seq"]

            if state["last_seq"] is not None:
                expected = state["last_seq"] + 1

                if first_seq > expected:
                    state["gaps"].append({
                        "from": expected,
                        "to": first_seq - 1,
                        "detected_at": int(time.time()),
                    })

            append_records(room, new_records)

            state["last_seq"] = new_records[-1]["seq"]
            state["records"] += len(new_records)

            save_state(room, state)

        print(
            room,
            "new:",
            len(new_records),
            "last_seq:",
            state["last_seq"],
            "total:",
            state["records"],
            "gaps:",
            len(state["gaps"]),
        )


def main():
    rooms = [
        "lobby",
        "technocore",
        "meta",
        "flop-network",
        "inference-agents",
    ]

    threads = []

    for room in rooms:
        thread = threading.Thread(
            target=follow_room,
            args=(room,),
            daemon=True,
            name=f"chronicle-{room}",
        )
        thread.start()
        threads.append(thread)

    print("CHRONICLE RUNNING:", ", ".join(rooms))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print("CHRONICLE STOPPED")


if __name__ == "__main__":
    main()
