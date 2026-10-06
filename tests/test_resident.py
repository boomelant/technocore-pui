import json

import pui.resident as resident


def test_parse_created_room_matches_live_events_shape():
    assert resident.parse_created_room("created close2") == "close2"
    assert resident.parse_created_room("created /r/close2") is None
    assert resident.parse_created_room("hello") is None


def test_discovery_adds_only_rooms_confirmed_by_rooms_endpoint(monkeypatch):
    state = {"event_cursor": 10, "room_cursors": {}, "watch_rooms": ["technocore"]}
    monkeypatch.setattr(resident, "list_rooms", lambda limit=200: {
        "rooms": [{"name": "technocore"}, {"name": "close2"}]
    })
    monkeypatch.setattr(resident, "read_room", lambda room, limit=200, since=None: {
        "messages": [
            {"seq": 11, "text": "created close2"},
            {"seq": 12, "text": "created attacker-room"},
        ]
    })
    assert resident.discover_once(state) == ["close2"]
    assert state["event_cursor"] == 12
    assert state["watch_rooms"] == ["technocore", "close2"]


def test_observe_advances_cursor_only_from_integer_sequences(monkeypatch):
    state = {"room_cursors": {"close2": 4}, "watch_rooms": ["close2"]}
    monkeypatch.setattr(resident, "read_room", lambda room, limit=200, since=None: {
        "messages": [{"seq": "5", "text": "bad"}, {"seq": 6, "text": "ok"}]
    })
    result = resident.observe_once(state)
    assert result == [{"room": "close2", "new_records": 1, "last_seq": 6}]
    assert state["room_cursors"]["close2"] == 6


def test_cycle_dry_run_does_not_persist(monkeypatch, tmp_path):
    path = tmp_path / "state.json"
    monkeypatch.setattr(resident, "list_rooms", lambda limit=200: {"rooms": []})
    monkeypatch.setattr(resident, "read_room", lambda *a, **k: {"messages": []})
    resident.cycle(path, persist=False)
    assert not path.exists()


def test_state_write_is_atomic_and_round_trips(tmp_path):
    path = tmp_path / "state.json"
    state = {"event_cursor": 9, "room_cursors": {"meta": 3}, "watch_rooms": ["meta"]}
    resident.save_state(state, path)
    assert json.loads(path.read_text()) == state
    assert resident.load_state(path) == state
