from pui import chronicle


def test_poll_room_does_not_advance_cursor_across_gap(monkeypatch, tmp_path):
    monkeypatch.setattr(chronicle, "DATA_DIR", tmp_path)

    room = "technocore"
    initial_state = {
        "room": room,
        "first_seq": 1,
        "last_seq": 100,
        "records": 100,
        "gaps": [],
    }
    chronicle.save_state(room, initial_state)

    monkeypatch.setattr(
        chronicle,
        "read_room",
        lambda *args, **kwargs: {
            "messages": [{"seq": seq} for seq in range(151, 351)]
        },
    )

    appended = []
    monkeypatch.setattr(
        chronicle,
        "append_records",
        lambda room_name, records: appended.append((room_name, records)),
    )

    chronicle.poll_room(room)

    state = chronicle.load_state(room)
    assert state["last_seq"] == 100
    assert state["records"] == 100
    assert appended == []
    assert len(state["gaps"]) == 1
    assert state["gaps"][0]["from"] == 101
    assert state["gaps"][0]["to"] == 150
