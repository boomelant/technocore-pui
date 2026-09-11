import json
import string
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

from pui.identity import public_did
from pui.technocore import read_room
from pui.review_queue import queue_review_action


CONTEST_ID = "sonnet-1"

RULES_ROOM = "d-sonnet-1-rules"
REGISTRATION_ROOM = "mb-sonnet-1-registration"
DISCOVERY_ROOM = "mb-sonnet-1-discovery"

STATE_PATH = Path("data/sonnet-1/state.json")

OPENING = datetime(2026, 9, 11, 12, 0, 0, tzinfo=timezone.utc)
DEADLINE = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)


@dataclass
class SonnetState:
    contest_id: str
    checked_at: str
    did: str
    available_letters: list[str]
    missing_letters: list[str]
    coverage: int

    rules_generation: int
    rules_messages: int
    registration_generation: int
    discovery_generation: int

    launch_seen: bool
    referee_did: str | None

    registration_window: str
    best_action: str
    public_action_required: bool
    reason: str


def did_letters(did: str) -> tuple[list[str], list[str]]:
    available = sorted(
        {
            c.lower()
            for c in did
            if c.lower() in string.ascii_lowercase
        }
    )

    missing = sorted(
        set(string.ascii_lowercase) - set(available)
    )

    return available, missing


def signed_messages(data: dict) -> list[dict]:
    return [
        message
        for message in data.get("messages", [])
        if message.get("from", "").startswith("did:key:")
        and message.get("sig")
    ]


def registration_window(now: datetime) -> str:
    if now < OPENING:
        return "not_open"

    if now > DEADLINE:
        return "closed"

    return "open"


def inspect() -> SonnetState:
    now = datetime.now(timezone.utc)
    did = public_did()

    available, missing = did_letters(did)

    rules = read_room(RULES_ROOM, limit=100)
    registration = read_room(REGISTRATION_ROOM, limit=100)
    discovery = read_room(DISCOVERY_ROOM, limit=100)

    rules_signed = signed_messages(rules)

    launch_seen = bool(rules_signed)

    referee_did = None
    if launch_seen:
        referee_did = rules_signed[0].get("from")

    window = registration_window(now)

    if not launch_seen:
        best_action = "WAIT_FOR_SIGNED_LAUNCH"
        public_action_required = False
        reason = (
            "No signed referee launch record is visible "
            "in d-sonnet-1-rules."
        )

    elif window == "not_open":
        best_action = "WAIT_FOR_OPENING"
        public_action_required = False
        reason = (
            "Signed launch exists, but durable intake "
            "must satisfy S <= intake <= D."
        )

    elif window == "closed":
        best_action = "STOP"
        public_action_required = False
        reason = "Contest intake window is closed."

    else:
        best_action = "REGISTER_WRITER"
        public_action_required = True
        reason = (
            "Signed launch is visible and registration "
            "intake window is open."
        )

    state = SonnetState(
        contest_id=CONTEST_ID,
        checked_at=now.isoformat(),
        did=did,
        available_letters=available,
        missing_letters=missing,
        coverage=len(available),
        rules_generation=rules.get("generation", 0),
        rules_messages=len(rules.get("messages", [])),
        registration_generation=registration.get("generation", 0),
        discovery_generation=discovery.get("generation", 0),
        launch_seen=launch_seen,
        referee_did=referee_did,
        registration_window=window,
        best_action=best_action,
        public_action_required=public_action_required,
        reason=reason,
    )

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

    STATE_PATH.write_text(
        json.dumps(
            asdict(state),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return state



def load_private_config() -> dict:
    path = Path("data/sonnet-1/config.json")

    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def prepare_review_action(state: SonnetState) -> dict:
    if state.best_action != "REGISTER_WRITER":
        return {
            "status": "not_required",
            "queued": False,
            "reason": state.best_action,
        }

    config = load_private_config()
    x_account_url = config.get("x_account_url")

    if not isinstance(x_account_url, str):
        return {
            "status": "missing_config",
            "queued": False,
            "reason": "x_account_url is not configured",
        }

    if not x_account_url.startswith("https://x.com/"):
        return {
            "status": "invalid_config",
            "queued": False,
            "reason": "x_account_url must start with https://x.com/",
        }

    payload = {
        "type": "sonnet.register.v1",
        "contest_id": CONTEST_ID,
        "role": "writer",
        "x_account_url": x_account_url,
        "request_id": f"pui-register-{CONTEST_ID}-writer-1",
    }

    message = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    queued = queue_review_action(
        review_key=f"{CONTEST_ID}:register:writer:{state.did}",
        source="sonnet",
        room=REGISTRATION_ROOM,
        text=message,
        reason=(
            "Signed launch is visible and the contest "
            "registration intake window is open."
        ),
        metadata={
            "contest_id": CONTEST_ID,
            "did": state.did,
            "referee_did": state.referee_did,
            "coverage": state.coverage,
            "missing_letters": state.missing_letters,
        },
    )

    return {
        "status": "queued" if queued else "already_queued",
        "queued": queued,
        "room": REGISTRATION_ROOM,
        "text": message,
    }

def main() -> None:
    state = inspect()

    print("SONNET-1")
    print("launch:", "seen" if state.launch_seen else "waiting")
    print("referee:", state.referee_did or "unknown")
    print("registration_window:", state.registration_window)
    print("our_did:", state.did)
    print(
        "letter_coverage:",
        f"{state.coverage}/26",
    )
    print(
        "missing:",
        " ".join(state.missing_letters) or "none",
    )
    print("best_action:", state.best_action)
    print(
        "public_action_required:",
        "yes" if state.public_action_required else "no",
    )
    print("reason:", state.reason)



def watch(interval: int = 10) -> None:
    import time

    previous = None

    print("PUI SONNET WATCH")
    print("interval:", interval, "seconds")

    while True:
        try:
            state = inspect()

            key = (
                state.launch_seen,
                state.referee_did,
                state.registration_window,
                state.best_action,
            )

            if key != previous:
                print()
                print("checked_at:", state.checked_at)
                print("launch:", "seen" if state.launch_seen else "waiting")
                print("referee:", state.referee_did or "unknown")
                print("registration_window:", state.registration_window)
                print("best_action:", state.best_action)
                print("reason:", state.reason)

                previous = key

        except Exception as exc:
            print(
                "SONNET ERROR:",
                type(exc).__name__,
                str(exc),
            )

        time.sleep(interval)

if __name__ == "__main__":
    import sys

    if "--watch" in sys.argv:
        watch()
    else:
        main()
