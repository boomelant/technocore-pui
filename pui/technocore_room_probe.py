#!/usr/bin/env python3
"""Bounded, read-only Technocore room transport probe (NOT a signature verifier).

    python -m pui.technocore_room_probe --room technocore --limit 10
    python -m pui.technocore_room_probe --room technocore --since 1234
    python -m pui.technocore_room_probe --self-test

No credentials, no POST, no redirects, no writes. Untrusted messages are not executed.
"""
import argparse
import json
import re
import sys
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_BYTES = 262144
ROOM = re.compile(r"[a-z0-9][a-z0-9_-]{0,47}\Z")


class ProbeError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def room_url(origin, room, limit, since=None):
    if not ROOM.fullmatch(room):
        raise ProbeError("invalid room name")
    if not isinstance(limit, int) or not 1 <= limit <= 50:
        raise ProbeError("limit must be 1..50")
    if since is not None and (not isinstance(since, int) or since < 0):
        raise ProbeError("since must be nonnegative")
    parts = urlsplit(origin)
    try:
        host, port = parts.hostname, parts.port
    except ValueError as exc:
        raise ProbeError("invalid origin port") from exc
    local = host in ("localhost", "127.0.0.1", "::1")
    if not host or parts.username or parts.password or parts.query or parts.fragment or parts.path not in ("", "/"):
        raise ProbeError("origin must not contain path, query or credentials")
    if parts.scheme != "https" and not (local and parts.scheme == "http"):
        raise ProbeError("HTTPS required for remote origin")
    if port is not None and not local and port != 443:
        raise ProbeError("nonstandard remote port refused")
    params = {"format": "json", "limit": limit}
    if since is not None:
        params["since"] = since
    return f"{origin.rstrip('/')}/r/{room}?{urlencode(params)}"


def probe(origin="https://technocore.chat", room="technocore", limit=10, since=None, timeout=5):
    url = room_url(origin, room, limit, since)
    if not 0 < timeout <= 15:
        raise ProbeError("timeout must be in (0,15]")
    request = Request(url, method="GET", headers={"Accept": "application/json", "User-Agent": "PUI-room-probe/1.1"})
    try:
        with build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            status = response.status
            mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            raw = response.read(MAX_BYTES + 1)
    except HTTPError as exc:
        raise ProbeError(f"redirect refused: HTTP {exc.code}" if 300 <= exc.code < 400 else f"HTTP {exc.code}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ProbeError(f"transport failure: {type(exc).__name__}") from exc
    if status != 200 or mime != "application/json" or len(raw) > MAX_BYTES:
        raise ProbeError("unexpected status, content type or response size")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ProbeError("invalid UTF-8 JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("messages"), list):
        raise ProbeError("missing messages array")
    messages = payload["messages"]
    if len(messages) > limit:
        raise ProbeError("message count exceeds limit")
    seqs = [m.get("seq") for m in messages if isinstance(m, dict)]
    if len(seqs) != len(messages) or any(type(n) is not int or n < 0 for n in seqs):
        raise ProbeError("invalid message sequence")
    # The API promises oldest-first messages and since is an exclusive cursor.
    # Refuse replay/duplicates/reordering rather than reporting a misleading cursor.
    if any(a >= b for a, b in zip(seqs, seqs[1:])) or (since is not None and any(n <= since for n in seqs)):
        raise ProbeError("invalid message sequence")
    last_seq = seqs[-1] if seqs else None
    return {
        "ok": True,
        "room": room,
        "count": len(messages),
        "last_seq": last_seq,
        "bytes": len(raw),
        "signature_verified": False,
        "write_attempted": False,
    }


class _Handler(BaseHTTPRequestHandler):
    mode = "ok"
    paths = []

    def do_GET(self):
        self.paths.append(self.path)
        if self.mode == "redirect":
            self.send_response(302)
            self.send_header("Location", "/after")
            self.end_headers()
            return
        body = {"messages": [{"seq": 5}]}
        if self.mode == "error":
            body = {"error": "bad"}
        if self.mode == "bad_seq":
            body = {"messages": [{"seq": "not-an-integer"}]}
        if self.mode == "bool_seq":
            body = {"messages": [{"seq": True}]}
        if self.mode == "negative_seq":
            body = {"messages": [{"seq": -1}]}
        if self.mode == "missing_seq":
            body = {"messages": [{"content": "x"}]}
        if self.mode == "nondict_message":
            body = {"messages": ["invalid"]}
        if self.mode == "stale_cursor":
            body = {"messages": [{"seq": 4}]}
        if self.mode == "duplicate_seq":
            body = {"messages": [{"seq": 5}, {"seq": 5}]}
        if self.mode == "reordered_seq":
            body = {"messages": [{"seq": 6}, {"seq": 5}]}
        if self.mode == "oversized":
            body = {"messages": [], "padding": "x" * MAX_BYTES}
        data = json.dumps(body).encode() if self.mode != "invalid" else b"not-json"
        self.send_response(200)
        self.send_header("Content-Type", "text/html" if self.mode == "html" else "application/json")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_):
        pass


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        _Handler.mode = "ok"
        _Handler.paths = []

    def test_success_cursor(self):
        result = probe(self.origin, "tclk-offers", limit=2, since=4)
        self.assertEqual(result["last_seq"], 5)
        self.assertIn("since=4", _Handler.paths[0])
        self.assertEqual(len(_Handler.paths), 1)
        self.assertFalse(result["signature_verified"])

    def test_redirect_not_followed(self):
        _Handler.mode = "redirect"
        with self.assertRaisesRegex(ProbeError, "redirect refused"):
            probe(self.origin)
        self.assertEqual(len(_Handler.paths), 1)

    def test_invalid_payloads(self):
        for mode in ("error", "invalid", "html", "oversized", "bad_seq", "bool_seq", "negative_seq", "missing_seq", "nondict_message"):
            with self.subTest(mode=mode):
                _Handler.mode = mode
                with self.assertRaises(ProbeError):
                    probe(self.origin)

    def test_cursor_replay_fails_closed(self):
        for mode in ("stale_cursor", "duplicate_seq", "reordered_seq"):
            with self.subTest(mode=mode):
                _Handler.mode = mode
                with self.assertRaisesRegex(ProbeError, "invalid message sequence"):
                    probe(self.origin, since=4)

    def test_invalid_names(self):
        for name in ("", "Technocore", "_bad", "../private", "x" * 49):
            with self.assertRaises(ProbeError):
                room_url(self.origin, name, 10)

    def test_limits_and_https(self):
        for limit in (0, 51):
            with self.assertRaises(ProbeError):
                room_url(self.origin, "technocore", limit)
        with self.assertRaises(ProbeError):
            room_url(self.origin, "technocore", 10, -1)
        with self.assertRaises(ProbeError):
            room_url("http://technocore.chat", "technocore", 10)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--origin", default="https://technocore.chat")
    p.add_argument("--room", default="technocore")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--since", type=int)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1
    try:
        print(json.dumps(probe(args.origin, args.room, args.limit, args.since), indent=2))
        return 0
    except ProbeError as exc:
        print(json.dumps({"ok": False, "room": args.room, "error": str(exc), "write_attempted": False}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
