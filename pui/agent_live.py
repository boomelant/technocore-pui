import json
import time
from datetime import datetime, timezone
from pathlib import Path

from pui.agent_scan import ROOMS, scan_room
from pui.opportunity import (
    opportunity_snapshot,
    discover_latest_executable_opportunity,
)
from pui.opportunity_state import write_opportunity_state
from pui.technocore import read_room, get_text
from pui.task_runner import process_opportunity
from pui.sonnet import (
    inspect as inspect_sonnet,
    prepare_review_action as prepare_sonnet_review_action,
)


HEALTH_PATH = Path("data/agent-health.json")
OPPORTUNITY_INTERVAL = 60
SONNET_INTERVAL = 30


def scan_opportunity_once() -> dict:
    result = opportunity_snapshot(read_room)
    write_opportunity_state(result)
    return result


def execute_opportunity_once() -> dict:
    candidate = discover_latest_executable_opportunity(
        read_room,
        get_text,
    )

    if candidate.get("status") != "executable":
        return {
            "status": "none",
            "executed": False,
        }

    opportunity = candidate.get("opportunity")

    if opportunity is None:
        return {
            "status": "none",
            "executed": False,
        }

    result = process_opportunity(
        opportunity,
        get_text,
    )

    return {
        **result,
        "executed": result.get("status") == "completed",
        "offer_id": opportunity.offer_id,
    }


def opportunity_cycle_once() -> dict:
    snapshot = scan_opportunity_once()
    execution = execute_opportunity_once()

    return {
        "snapshot": snapshot,
        "execution": execution,
    }


def write_health(
    started_at: str,
    last_scan_at: str,
    total_scanned: int,
    total_queued: int,
    room_stats: dict,
    sonnet_state: dict | None = None,
) -> None:
    HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "protocol": "PUI-AGENT-HEALTH/1",
        "started_at": started_at,
        "last_scan_at": last_scan_at,
        "total_scanned": total_scanned,
        "total_queued": total_queued,
        "rooms": room_stats,
        "sonnet": sonnet_state,
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

    last_opportunity_scan = 0.0
    last_sonnet_scan = 0.0
    last_sonnet_action = None
    sonnet_health = None

    while True:
        room_stats = {}

        now_monotonic = time.monotonic()

        if now_monotonic - last_opportunity_scan >= OPPORTUNITY_INTERVAL:
            try:
                cycle = opportunity_cycle_once()

                snapshot = cycle.get("snapshot", {})
                execution = cycle.get("execution", {})

                print(
                    "opportunity:",
                    snapshot.get("status"),
                    snapshot.get("decision"),
                )

                print(
                    "execution:",
                    execution.get("status"),
                    execution.get("offer_id"),
                )

            except Exception as exc:
                print(
                    "opportunity ERROR:",
                    type(exc).__name__,
                    str(exc),
                )

            last_opportunity_scan = now_monotonic

        if now_monotonic - last_sonnet_scan >= SONNET_INTERVAL:
            try:
                sonnet = inspect_sonnet()
                review = prepare_sonnet_review_action(sonnet)
                sonnet_health = {
                    "checked_at": sonnet.checked_at,
                    "launch_seen": sonnet.launch_seen,
                    "referee_did": sonnet.referee_did,
                    "registration_window": sonnet.registration_window,
                    "best_action": sonnet.best_action,
                    "public_action_required": sonnet.public_action_required,
                    "reason": sonnet.reason,
                    "coverage": sonnet.coverage,
                    "missing_letters": sonnet.missing_letters,
                    "review_status": review.get("status"),
                    "review_queued": review.get("queued", False),
                }

                if sonnet.best_action != last_sonnet_action:
                    print(
                        "sonnet:",
                        sonnet.best_action,
                        "| launch:",
                        "seen" if sonnet.launch_seen else "waiting",
                        "| referee:",
                        sonnet.referee_did or "unknown",
                    )
                    print("sonnet reason:", sonnet.reason)

                    last_sonnet_action = sonnet.best_action

            except Exception as exc:
                print(
                    "sonnet ERROR:",
                    type(exc).__name__,
                    str(exc),
                )

            last_sonnet_scan = now_monotonic

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
            sonnet_state=sonnet_health,
        )

        time.sleep(interval)


if __name__ == "__main__":
    main()
