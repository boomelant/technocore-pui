import json
import time
from datetime import datetime, timezone
from pathlib import Path

from pui.agent_scan import ROOMS, scan_room


HEALTH_PATH = Path("data/agent-health.json")


def write_health(
    started_at: str,
    last_scan_at: str,
    total_scanned: int,
    total_queued: int,
    room_stats: dict,
) -> None:
    HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "protocol": "PUI-AGENT-HEALTH/1",
        "started_at": started_at,
        "last_scan_at": last_scan_at,
        "total_scanned": total_scanned,
        "total_queued": total_queued,
        "rooms": room_stats,
    }

    HEALTH_PATH.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main(interval: int = 15):
    started_at = datetime.now(timezone.utc).isoformat()

    total_scanned = 0
    total_queued = 0

    print("PUI AGENT LIVE RUNNING")
    print("rooms:", ", ".join(ROOMS))
    print("scan interval:", interval, "seconds")

    while True:
        room_stats = {}

        for room in ROOMS:
            try:
                scanned, queued, last_seq = scan_room(room)

                total_scanned += scanned
                total_queued += queued

                room_stats[room] = {
                    "scanned": scanned,
                    "queued": queued,
                    "last_processed_seq": last_seq,
                    "status": "ok",
                }

                if scanned or queued:
                    print(
                        room,
                        "scanned:",
                        scanned,
                        "queued:",
                        queued,
                        "last_processed:",
                        last_seq,
                    )

            except Exception as exc:
                room_stats[room] = {
                    "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                }

                print(
                    room,
                    "ERROR:",
                    type(exc).__name__,
                    str(exc),
                )

        last_scan_at = datetime.now(timezone.utc).isoformat()

        write_health(
            started_at=started_at,
            last_scan_at=last_scan_at,
            total_scanned=total_scanned,
            total_queued=total_queued,
            room_stats=room_stats,
        )

        time.sleep(interval)


if __name__ == "__main__":
    main()
