import json
from datetime import datetime, timezone
from pathlib import Path

from .config import DATA_DIR, DID
from .identity import sign_text
from .protocol import canonical_json, sha256_text


def build_report(
    rooms,
    room_analyses,
    semantic_clusters,
    cross_room_dids,
):
    report = {
        "protocol": "PUI/1",
        "artifact": "technocore-coordination-report",
        "author": DID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "rooms": rooms,
        "summary": {
            "rooms_scanned": len(rooms),
            "semantic_clusters": len(semantic_clusters),
            "cross_room_dids": len(cross_room_dids),
        },
        "room_analysis": room_analyses,
        "top_semantic_clusters": semantic_clusters[:20],
        "top_cross_room_dids": cross_room_dids[:50],
        "methodology": {
            "template_normalization": True,
            "semantic_similarity": "token Jaccard",
            "semantic_threshold": 0.72,
            "minimum_cluster_dids": 4,
            "important_note": (
                "Coordination signals are heuristic. "
                "They do not prove common ownership or malicious intent."
            ),
        },
    }

    unsigned = canonical_json(report)
    report["report_hash"] = sha256_text(unsigned)

    canonical_for_signature = canonical_json(report)
    report["signature"] = sign_text(canonical_for_signature)

    return report


def save_report(report):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = DATA_DIR / f"pui-report-{stamp}.json"

    path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return path
