#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

case "${1:-}" in
  resident-install)
    chmod +x INSTALUJ_RESIDENT.command URUCHOM_RESIDENT.command ZATRZYMAJ_RESIDENT.command
    exec ./INSTALUJ_RESIDENT.command
    ;;
  resident)
    chmod +x URUCHOM_RESIDENT.command
    exec ./URUCHOM_RESIDENT.command
    ;;
  resident-stop)
    chmod +x ZATRZYMAJ_RESIDENT.command
    exec ./ZATRZYMAJ_RESIDENT.command
    ;;
esac

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
