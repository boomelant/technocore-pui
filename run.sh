#!/bin/bash
set -e

cd "$(dirname "$0")"

source .venv/bin/activate

echo
echo "PUI — Technocore Coordination Scanner"
echo "======================================"
echo

python -m pui.main

python - <<'PY'
from pui.dashboard import generate_dashboard

dashboard, report = generate_dashboard()

print()
print("Dashboard:", dashboard)
print("Report:", report)
PY

open data/dashboard.html
