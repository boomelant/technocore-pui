from pathlib import Path

from .technocore import read_room
from .snapshot import save_snapshot
from .scoring import analyze_messages
from .coordination import find_semantic_clusters, did_cross_room_activity
from .history import load_snapshot, compare_snapshots
from .report import build_report, save_report


ROOMS = [
    "meta",
    "lobby",
    "technocore",
    "flop-network",
    "inference-agents",
]


def main():
    print()
    print("PUI / Proof of Useful Interaction")
    print("Technocore Coordination Scanner")
    print("=" * 72)

    room_messages = {}
    room_analyses = {}

    for room in ROOMS:
        print(f"Scanning: {room}")

        data = read_room(room, 200)
        messages = data["messages"]

        room_messages[room] = messages
        room_analyses[room] = analyze_messages(messages)

    snapshot_path = save_snapshot(room_messages)

    clusters = find_semantic_clusters(
        room_messages,
        threshold=0.72,
        min_dids=4,
    )

    cross_room = did_cross_room_activity(room_messages)

    report = build_report(
        ROOMS,
        room_analyses,
        clusters,
        cross_room,
    )

    report_path = save_report(report)

    print()
    print("ROOM SIGNALS")
    print("-" * 72)

    ranked = sorted(
        room_analyses.items(),
        key=lambda x: x[1]["coordination_risk"],
        reverse=True,
    )

    for room, data in ranked:
        print(
            f"{room:20} "
            f"signal={data['signal_score']:6.2f} "
            f"coord={data['coordination_risk']:6.2f} "
            f"repeat={data['repetition_ratio']:6.2%}"
        )

    print()
    print("NETWORK")
    print("-" * 72)

    print("semantic clusters:", len(clusters))
    print("cross-room DIDs:", len(cross_room))

    snapshots = sorted(Path("data").glob("snapshot-*.json"))

    if len(snapshots) >= 2:
        old_snapshot = load_snapshot(snapshots[-2])
        new_snapshot = load_snapshot(snapshots[-1])

        history = compare_snapshots(
            old_snapshot,
            new_snapshot,
        )

        print("recurring DIDs:", history["recurring_dids"])
        print(
            "recurring DID ratio:",
            f"{history['recurring_did_ratio']:.2%}",
        )
        print(
            "persistent patterns:",
            len(history["persistent_patterns"]),
        )
        print(
            "recurring cross-room DIDs:",
            len(history["recurring_cross_room"]),
        )

    print()
    print("SIGNED ARTIFACT")
    print("-" * 72)

    print("snapshot:", snapshot_path)
    print("report:", report_path)
    print("hash:", report["report_hash"])
    print("signature length:", len(report["signature"]))

    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
