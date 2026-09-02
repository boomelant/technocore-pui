import json

import pui.cross_room as cross_room


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_top_cross_room_dids(monkeypatch, tmp_path):
    monkeypatch.setattr(cross_room, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        cross_room,
        "ROOMS",
        ("lobby", "technocore", "meta"),
    )

    write_jsonl(
        tmp_path / "lobby.jsonl",
        [
            {"from": "did:key:A"},
            {"from": "did:key:A"},
            {"from": "did:key:B"},
        ],
    )

    write_jsonl(
        tmp_path / "technocore.jsonl",
        [
            {"from": "did:key:A"},
            {"from": "did:key:C"},
        ],
    )

    write_jsonl(
        tmp_path / "meta.jsonl",
        [
            {"from": "did:key:A"},
            {"from": "did:key:B"},
        ],
    )

    rows = cross_room.top_cross_room_dids(limit=10)

    assert rows[0]["did"] == "did:key:A"
    assert rows[0]["room_count"] == 3
    assert rows[0]["messages"] == 4

    assert rows[1]["did"] == "did:key:B"
    assert rows[1]["room_count"] == 2
    assert rows[1]["messages"] == 2

    assert all(row["did"] != "did:key:C" for row in rows)
