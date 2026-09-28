import json

import pui.agent_scan as agent_scan


def test_scan_room_rejects_boolean_seq_but_accepts_integer(tmp_path, monkeypatch):
    chronicle = tmp_path / "chronicle"
    chronicle.mkdir()
    room = "technocore"
    path = chronicle / f"{room}.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps({"seq": True, "kind": "invalid"}),
                json.dumps({"seq": 7, "kind": "valid"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    queued = []
    checkpoints = []
    monkeypatch.setattr(agent_scan, "DATA_DIR", chronicle)
    monkeypatch.setattr(agent_scan, "get_last_processed", lambda _room: None)
    monkeypatch.setattr(agent_scan, "queue_event", lambda record: queued.append(record.copy()) or True)
    monkeypatch.setattr(
        agent_scan,
        "set_last_processed",
        lambda checkpoint_room, seq: checkpoints.append((checkpoint_room, seq)),
    )

    scanned, queued_count, highest_seq = agent_scan.scan_room(room)

    assert scanned == 1
    assert queued_count == 1
    assert highest_seq == 7
    assert [record["seq"] for record in queued] == [7]
    assert checkpoints == [(room, 7)]
