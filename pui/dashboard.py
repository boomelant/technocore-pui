import html
import json
from pathlib import Path

from .config import DATA_DIR


def latest_report():
    reports = sorted(DATA_DIR.glob("pui-report-*.json"))
    if not reports:
        raise FileNotFoundError("No PUI reports found.")

    path = reports[-1]
    data = json.loads(path.read_text(encoding="utf-8"))
    return path, data


def generate_dashboard():
    report_path, report = latest_report()

    rows = []
    analyses = report["room_analysis"]

    ranked = sorted(
        analyses.items(),
        key=lambda x: x[1]["coordination_risk"],
        reverse=True,
    )

    for room, data in ranked:
        rows.append(
            "<tr>"
            f"<td>{html.escape(room)}</td>"
            f"<td>{data['messages']}</td>"
            f"<td>{data['unique_authors']}</td>"
            f"<td>{data['repetition_ratio']:.1%}</td>"
            f"<td>{data['signal_score']:.2f}</td>"
            f"<td>{data['coordination_risk']:.2f}</td>"
            "</tr>"
        )

    cluster_rows = []

    for item in report["top_lexical_clusters"][:10]:
        cluster_rows.append(
            "<tr>"
            f"<td>{item['did_count']}</td>"
            f"<td>{item['message_count']}</td>"
            f"<td>{item['room_count']}</td>"
            f"<td>{html.escape(', '.join(item['rooms']))}</td>"
            f"<td>{html.escape(item['example'])}</td>"
            "</tr>"
        )

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PUI Technocore Scanner</title>
<style>
body {{
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    margin: 40px;
    background: #111;
    color: #eee;
}}
h1, h2 {{ margin-bottom: 8px; }}
small {{ color: #999; }}
.card {{
    background: #1b1b1b;
    border: 1px solid #333;
    border-radius: 12px;
    padding: 20px;
    margin: 20px 0;
}}
table {{
    width: 100%;
    border-collapse: collapse;
}}
th, td {{
    padding: 10px;
    border-bottom: 1px solid #333;
    text-align: left;
    vertical-align: top;
}}
th {{ color: #aaa; }}
code {{
    word-break: break-all;
    color: #ddd;
}}
.warning {{
    color: #f0c674;
}}
</style>
</head>
<body>

<h1>PUI / Proof of Useful Interaction</h1>
<small>Technocore Coordination Scanner</small>

<div class="card">
<h2>Signed Artifact</h2>
<p><strong>Author DID</strong><br><code>{html.escape(report['author'])}</code></p>
<p><strong>Report hash</strong><br><code>{html.escape(report['report_hash'])}</code></p>
<p><strong>Created</strong><br>{html.escape(report['created_at'])}</p>
</div>

<div class="card">
<h2>Network Summary</h2>
<p>Rooms scanned: {report['summary']['rooms_scanned']}</p>
<p>Lexical clusters: {report['summary']['lexical_clusters']}</p>
<p>Cross-room DIDs: {report['summary']['cross_room_dids']}</p>
</div>

<div class="card">
<h2>Room Signals</h2>
<table>
<thead>
<tr>
<th>Room</th>
<th>Messages</th>
<th>Authors</th>
<th>Repetition</th>
<th>Signal</th>
<th>Coordination Risk</th>
</tr>
</thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</div>

<div class="card">
<h2>Top Coordination Patterns</h2>
<table>
<thead>
<tr>
<th>DIDs</th>
<th>Messages</th>
<th>Rooms</th>
<th>Room Names</th>
<th>Example</th>
</tr>
</thead>
<tbody>
{''.join(cluster_rows)}
</tbody>
</table>
</div>

<div class="card warning">
<strong>Important:</strong>
These scores are heuristic coordination signals.
They do not prove common ownership, malicious intent, or Sybil control.
</div>

</body>
</html>
"""

    output = DATA_DIR / "dashboard.html"
    output.write_text(page, encoding="utf-8")

    return output, report_path
