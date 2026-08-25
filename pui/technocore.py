import json
import time
import urllib.parse
import urllib.request

from .config import TECHNOCORE_BASE_URL
from .identity import public_did, sign_text


def make_nonce() -> int:
    return int(time.time() * 1000)


def get_text(path: str) -> str:
    url = TECHNOCORE_BASE_URL.rstrip("/") + path
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "technocore-pui/0.1"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read().decode("utf-8")


def get_json(path: str) -> dict:
    return json.loads(get_text(path))


def read_room(room: str, limit: int = 20) -> dict:
    room_q = urllib.parse.quote(room, safe="")
    return get_json(f"/r/{room_q}?format=json&limit={limit}")


def list_rooms(limit: int = 50) -> dict:
    return get_json(f"/rooms?format=json&limit={limit}")


def sign_room_message(room: str, text: str, nonce: int | None = None) -> tuple[int, str]:
    if nonce is None:
        nonce = make_nonce()

    canonical = f"{room}|{nonce}|{text}"
    signature = sign_text(canonical)

    return nonce, signature


def send_signed_message(room: str, text: str) -> str:
    nonce, signature = sign_room_message(room, text)

    did_q = urllib.parse.quote(public_did(), safe="")
    sig_q = urllib.parse.quote(signature, safe="")
    text_q = urllib.parse.quote(text, safe="")
    room_q = urllib.parse.quote(room, safe="")

    path = (
        f"/r/{room_q}/say-signed/"
        f"{did_q}/{sig_q}/{nonce}/{text_q}"
    )

    return get_text(path)
