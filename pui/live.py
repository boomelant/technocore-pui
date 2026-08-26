import threading
import time

from pui.chronicle import follow_room
from pui.chronicle_status import main as write_status


ROOMS = [
    "lobby",
    "technocore",
    "meta",
    "flop-network",
    "inference-agents",
]


def status_loop(interval=60):
    while True:
        time.sleep(interval)

        try:
            write_status()
        except Exception as exc:
            print("STATUS ERROR:", exc)


def main():
    threads = []

    for room in ROOMS:
        thread = threading.Thread(
            target=follow_room,
            args=(room,),
            daemon=True,
            name=f"pui-live-{room}",
        )
        thread.start()
        threads.append(thread)

    status_thread = threading.Thread(
        target=status_loop,
        daemon=True,
        name="pui-live-status",
    )
    status_thread.start()

    print("PUI LIVE RUNNING")
    print("rooms:", ", ".join(ROOMS))
    print("dashboard status interval: 60s")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print("PUI LIVE STOPPED")


if __name__ == "__main__":
    main()
