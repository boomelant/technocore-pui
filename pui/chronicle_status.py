import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from pui.chronicle import coverage_stats, live_coverage_stats


DATA_DIR = Path("data/chronicle")

LOCAL_OUTPUT = Path("data/chronicle-status.json")
PUBLIC_OUTPUT = Path("public/chronicle-status.json")
DOCS_OUTPUT = Path("docs/chronicle-status.json")
AGENT_HEALTH = Path("data/agent-health.json")

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


def build_status():
    generated_at = datetime.now(timezone.utc)

    agent = {
        "status": "unknown",
        "last_scan_at": None,
        "total_scanned": 0,
        "total_queued": 0,
    }

    if AGENT_HEALTH.exists():
        try:
            raw = json.loads(AGENT_HEALTH.read_text(encoding="utf-8"))
            agent = {
                "status": "online",
                "last_scan_at": raw.get("last_scan_at"),
                "started_at": raw.get("started_at"),
                "total_scanned": raw.get("total_scanned", 0),
                "total_queued": raw.get("total_queued", 0),
            }
        except Exception:
            agent["status"] = "error"

    return {
        "protocol": "PUI-CHRONICLE-STATUS/1",
        "generated_at": generated_at.isoformat(),
        "observer": {
            "status": "online",
            "room_count": len(ROOMS),
        },
        "agent": agent,
        "rooms": [room_status(room) for room in ROOMS],
    }


def write_status(publish=False):
    status = build_status()
    rendered = json.dumps(status, indent=2)

    LOCAL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_OUTPUT.write_text(rendered, encoding="utf-8")

    print("CHRONICLE STATUS WRITTEN")
    print("local:", LOCAL_OUTPUT)

    if publish:
        PUBLIC_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        PUBLIC_OUTPUT.write_text(rendered, encoding="utf-8")

        DOCS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        DOCS_OUTPUT.write_text(rendered, encoding="utf-8")

        print("public:", PUBLIC_OUTPUT)
        print("pages:", DOCS_OUTPUT)

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--publish",
        action="store_true",
        help="also update public and GitHub Pages snapshots",
    )

    args = parser.parse_args()
    write_status(publish=args.publish)


if __name__ == "__main__":
    main()
