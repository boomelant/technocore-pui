from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STATE_PATH = Path("data/flop-readiness.json")

OFFICIAL_SOURCES = (
    "https://flop.finance/teaser/",
    "https://flop.finance/intro/agent/",
    "https://flop.finance/llms.txt",
)

ENDPOINT_PATTERNS = {
    "faucet": (
        r"https?://[^\s\"'<>]*faucet[^\s\"'<>]*",
        r"\bfaucet\s+(?:url|endpoint|live)\b",
    ),
    "rpc": (
        r"https?://[^\s\"'<>]*rpc[^\s\"'<>]*",
        r"\brpc\s+(?:url|endpoint)\b",
        r"\bchain\s*id\b",
    ),
    "inference": (
        r"https?://[^\s\"'<>]*(?:inference|session)[^\s\"'<>]*",
        r"\binference\s+(?:api|endpoint|url)\b",
    ),
}


def fetch_text(url: str, timeout: int = 10) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "PUI-FLOP-Readiness/1"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def detect_signals(text: str) -> dict:
    lower = text.lower()

    matches = {}
    for name, patterns in ENDPOINT_PATTERNS.items():
        found = []
        for pattern in patterns:
            found.extend(
                re.findall(pattern, lower, flags=re.IGNORECASE)
            )
        matches[name] = sorted(set(found))[:10]

    return {
        "faucet_evidence": matches["faucet"],
        "rpc_evidence": matches["rpc"],
        "inference_evidence": matches["inference"],
    }


def check_readiness() -> dict:
    previous = {}

    if STATE_PATH.exists():
        try:
            previous = json.loads(STATE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            previous = {}

    old_sources = previous.get("sources", {})
    sources = {}
    changed = []

    for url in OFFICIAL_SOURCES:
        try:
            text = fetch_text(url)
            digest = sha256_text(text)

            old_digest = (
                old_sources.get(url, {}).get("sha256")
                if isinstance(old_sources, dict)
                else None
            )

            if old_digest and old_digest != digest:
                changed.append(url)

            sources[url] = {
                "ok": True,
                "sha256": digest,
                "bytes": len(text.encode("utf-8")),
                "signals": detect_signals(text),
            }

        except Exception as exc:
            sources[url] = {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
            }

    result = {
        "protocol": "PUI-FLOP-READINESS/1",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "official_sources_only": True,
        "changed_sources": changed,
        "sources": sources,
    }

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )

    return result


def main():
    result = check_readiness()

    print(
        json.dumps(
            {
                "status": "ok",
                "changed_sources": result["changed_sources"],
                "sources_ok": sum(
                    1
                    for source in result["sources"].values()
                    if source.get("ok")
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
