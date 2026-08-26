import json
from datetime import datetime, timezone
from pathlib import Path

from pui.chronicle import coverage_stats, live_coverage_stats


DATA_DIR = Path("data/chronicle")
OUTPUT = Path("data/chronicle-status.json")
PUBLIC_OUTPUT = Path("public/chronicle-status.json")

ROOMS = [
    "lobby",
    "technocore",
    "meta",
    "flop-network",
    "inference-agents",
]


def room_status(room):
    path = DATA_DIR / f"{room}-state.json"

    if not path.exists():
        return {
            "room": room,
            "status": "no-data",
        }

    state = json.loads(path.read_text(encoding="utf-8"))

    historical = coverage_stats(state)
    epoch = live_coverage_stats(state)

    return {
        "room": room,
        "first_seq": state.get("first_seq"),
        "last_seq": state.get("last_seq"),
        "records": state.get("records", 0),
        "gaps": len(state.get("gaps", [])),
        "historical_coverage": round(historical["coverage"], 2),
        "epoch_coverage": round(epoch["coverage"], 2),
    }


def main():
    status = {
        "protocol": "PUI-CHRONICLE-STATUS/1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rooms": [room_status(room) for room in ROOMS],
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    rendered = json.dumps(status, indent=2)

    OUTPUT.write_text(
        rendered,
        encoding="utf-8",
    )

    PUBLIC_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    PUBLIC_OUTPUT.write_text(
        rendered,
        encoding="utf-8",
    )

    print("CHRONICLE STATUS WRITTEN")
    print("local:", OUTPUT)
    print("public:", PUBLIC_OUTPUT)

    for room in status["rooms"]:
        print(
            room["room"],
            "records:",
            room.get("records"),
            "historical:",
            room.get("historical_coverage"),
            "epoch:",
            room.get("epoch_coverage"),
        )


if __name__ == "__main__":
    main()
