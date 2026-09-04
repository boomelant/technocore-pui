from .task import Task


def task_from_queue_event(event: dict) -> Task:
    event_key = event.get("event_key")
    text = event.get("text")
    room = event.get("room")
    seq = event.get("seq")

    if not isinstance(event_key, str) or not event_key:
        raise ValueError("queue event requires event_key")

    if not isinstance(text, str):
        raise ValueError("queue event requires text")

    if not isinstance(room, str) or not room:
        raise ValueError("queue event requires room")

    if not isinstance(seq, int):
        raise ValueError("queue event requires integer seq")

    return Task(
        task_id=f"queue:{event_key}",
        task_type="text_analysis",
        payload={
            "text": text,
            "source_event_key": event_key,
            "source_room": room,
            "source_seq": seq,
        },
    )
