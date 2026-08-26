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
            "first_seq": None,
            "last_seq": None,
            "records": 0,
            "gaps": [],
        }

    state = json.loads(path.read_text(encoding="utf-8"))

    if "first_seq" not in state:
        state["first_seq"] = None

    return state


def save_state(room, state):
    path = DATA_DIR / f"{room}-state.json"
    path.write_text(
        json.dumps(state, indent=2),
        encoding="utf-8",
    )


def session_coverage_stats(
    state,
    session_start_seq,
    session_start_records,
    session_gap_count,
):
    if (
        session_start_seq is None
        or session_start_records is None
        or session_gap_count is None
    ):
        return {
            "expected": 0,
            "captured": 0,
            "missing": 0,
            "coverage": 100.0,
        }

    last_seq = state.get("last_seq")
    records = state.get("records", 0)
    gaps = state.get("gaps", [])

    if last_seq is None or last_seq < session_start_seq:
        return {
            "expected": 0,
            "captured": 0,
            "missing": 0,
            "coverage": 100.0,
        }

    expected = last_seq - session_start_seq + 1
    captured = records - session_start_records

    missing = 0

    for gap in gaps[session_gap_count:]:
        gap_from = max(gap["from"], session_start_seq)
        gap_to = min(gap["to"], last_seq)

        if gap_from <= gap_to:
            missing += gap_to - gap_from + 1

    if expected <= 0:
        coverage = 100.0
    else:
        coverage = max(
            0.0,
            min(100.0, captured / expected * 100.0),
        )

    return {
        "expected": expected,
        "captured": captured,
        "missing": missing,
        "coverage": coverage,
    }


def live_coverage_stats(state):
    live_start_seq = state.get("live_start_seq")
    live_start_records = state.get("live_start_records")
    last_seq = state.get("last_seq")
    records = state.get("records", 0)
    gaps = state.get("gaps", [])

    if live_start_seq is None or live_start_records is None or last_seq is None:
        return {
            "expected": 0,
            "captured": 0,
            "missing": 0,
            "coverage": 0.0,
        }

    if last_seq < live_start_seq:
        return {
            "expected": 0,
            "captured": 0,
            "missing": 0,
            "coverage": 100.0,
        }

    expected = last_seq - live_start_seq + 1
    captured = records - live_start_records

    missing = 0

    for gap in gaps:
        gap_from = max(gap["from"], live_start_seq)
        gap_to = min(gap["to"], last_seq)

        if gap_from <= gap_to:
            missing += gap_to - gap_from + 1

    if expected <= 0:
        coverage = 100.0
    else:
        coverage = max(
            0.0,
            min(100.0, captured / expected * 100.0),
        )

    return {
        "expected": expected,
        "captured": captured,
        "missing": missing,
        "coverage": coverage,
    }


def coverage_stats(state):
    first_seq = state.get("first_seq")
    last_seq = state.get("last_seq")
    records = state.get("records", 0)
    gaps = state.get("gaps", [])

    if first_seq is None or last_seq is None:
        return {
            "expected": 0,
            "captured": records,
            "missing": 0,
            "coverage": 0.0,
        }

    expected = last_seq - first_seq + 1

    missing = 0
    for gap in gaps:
        missing += gap["to"] - gap["from"] + 1

    if expected <= 0:
        coverage = 0.0
    else:
        coverage = max(0.0, min(100.0, records / expected * 100.0))

    return {
        "expected": expected,
        "captured": records,
        "missing": missing,
        "coverage": coverage,
    }




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

    session_start_seq = None
    session_start_records = None
    session_gap_count = None

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

            if state["first_seq"] is None:
                state["first_seq"] = new_records[0]["seq"]

            state["last_seq"] = new_records[-1]["seq"]
            state["records"] += len(new_records)

            save_state(room, state)

            if session_start_seq is None:
                session_start_seq = state["last_seq"] + 1
                session_start_records = state["records"]
                session_gap_count = len(state["gaps"])

        stats = coverage_stats(state)
        live_stats = live_coverage_stats(state)
        session_stats = session_coverage_stats(
            state,
            session_start_seq,
            session_start_records,
            session_gap_count,
        )

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
            "historical:",
            f'{stats["coverage"]:.2f}%',
            "epoch:",
            f'{live_stats["coverage"]:.2f}%',
            "session:",
            f'{session_stats["coverage"]:.2f}%',
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
