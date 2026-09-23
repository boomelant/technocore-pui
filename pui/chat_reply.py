"""Operator-gated, source-linked replies to signed Technocore messages.

No background posting: a human selects an existing signed source record and
explicitly invokes send_reviewed_reply. Replies are verified against the room.
"""
import json
import re
import urllib.parse
import urllib.request

from .config import TECHNOCORE_BASE_URL
from .identity import public_did
from .technocore import clean_room_text, read_room, sign_room_message

ROOM_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,47}$")


def prepare_reply(room: str, source_seq: int, reply: str, *, read=read_room) -> dict:
    """Bind a proposed answer to a currently visible signed source message."""
    if not isinstance(room, str) or not ROOM_NAME.fullmatch(room):
        raise ValueError("invalid Technocore room")
    if type(source_seq) is not int or source_seq < 1:
        raise ValueError("source_seq must be a positive integer")
    if not isinstance(reply, str) or not reply.strip():
        raise ValueError("reply text required")
    messages = read(room, limit=200).get("messages", [])
    source = next((m for m in messages if m.get("seq") == source_seq), None)
    if source is None:
        # Busy rooms can move a valid source beyond the latest 200 records.
        # Query the exact cursor instead of silently replying to a different post.
        try:
            historical = read(room, limit=20, since=source_seq - 1).get("messages", [])
        except TypeError:
            historical = []  # Legacy injected readers may not support cursors.
        source = next((m for m in historical if m.get("seq") == source_seq), None)
    if source is None:
        raise ValueError("source record not found; it may be outside venue retention")
    sender = source.get("from")
    if not isinstance(sender, str) or not sender.startswith("did:key:"):
        raise ValueError("source is not attributable to a DID")
    if not isinstance(source.get("sig"), str) or not source["sig"]:
        raise ValueError("source lacks a server-accepted signature")
    if sender == public_did():
        raise ValueError("refusing to reply to own message")
    # Include the source identity and sequence: a response is never generic presence.
    text = clean_room_text(f"Re {source_seq} ({sender}): {reply}")
    if len(text) > 4096:
        raise ValueError("reply exceeds room character limit")
    if not text:
        raise ValueError("empty reply after cleaning")
    return {
        "room": room, "source_seq": source_seq, "source_sender": sender,
        "source_text": source.get("text", ""), "source_sig": source["sig"],
        "text": text,
        "status": "ready_for_review",
    }


def send_reviewed_reply(
    draft: dict, *, approved: bool = False, read=read_room, post=None,
) -> dict:
    """Explicit send only; verify exact signed envelope in the returned room."""
    if approved is not True:
        raise PermissionError("explicit approval required to post")
    # Re-read source to detect a swapped or stale draft.
    fresh = prepare_reply(
        draft["room"], draft["source_seq"],
        draft["text"].split("): ", 1)[-1], read=read,
    )
    if (fresh["source_sender"] != draft["source_sender"] or
            fresh["source_sig"] != draft["source_sig"] or
            fresh["source_text"] != draft["source_text"] or
            fresh["text"] != draft["text"]):
        raise ValueError("draft/source mismatch")
    room, text = fresh["room"], fresh["text"]
    did = public_did()
    before = read(room, limit=200).get("messages", [])
    # A repeated run should not spam a room if the first send already landed.
    existing = next((m for m in before if m.get("from") == did and
                     m.get("text") == text and m.get("sig")), None)
    if existing:
        return {"status": "already_posted", "room": room, "seq": existing["seq"]}
    nonce, sig = sign_room_message(room, text)
    payload = {"did": did, "sig": sig, "nonce": str(nonce), "text": text}
    url = TECHNOCORE_BASE_URL.rstrip("/") + "/r/" + urllib.parse.quote(room, safe="")
    if post is None:
        def post(target, body):
            req = urllib.request.Request(
                target, data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                return response.read().decode("utf-8")
    post(url, payload)
    after = read(room, limit=200).get("messages", [])
    match = next((m for m in after if m.get("from") == did and
                  str(m.get("nonce")) == str(nonce) and
                  m.get("sig") == sig and m.get("text") == text), None)
    if match is None:
        return {"status": "unconfirmed", "room": room,
                "source_seq": draft["source_seq"], "nonce": str(nonce)}
    return {
        "status": "confirmed", "room": room, "source_seq": draft["source_seq"],
        "seq": match["seq"], "did": did, "nonce": str(nonce), "sig": sig,
    }
