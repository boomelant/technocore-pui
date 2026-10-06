#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"
PY="$ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then
  python3 -m venv .venv
  "$ROOT/.venv/bin/pip" install -r requirements.txt
fi
"$PY" -m pytest -q
mkdir -p "$HOME/Library/LaunchAgents" "$ROOT/data/logs"
PLIST="$HOME/Library/LaunchAgents/com.boomelant.pui-resident.plist"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.boomelant.pui-resident</string>
<key>ProgramArguments</key><array><string>$PY</string><string>-m</string><string>pui.resident</string><string>--interval</string><string>60</string></array>
<key>WorkingDirectory</key><string>$ROOT</string>
<key>RunAtLoad</key><true/>
<key>KeepAlive</key><true/>
<key>ThrottleInterval</key><integer>10</integer>
<key>StandardOutPath</key><string>$ROOT/data/logs/resident.out.log</string>
<key>StandardErrorPath</key><string>$ROOT/data/logs/resident.err.log</string>
</dict></plist>
EOF
plutil -lint "$PLIST"
launchctl bootout "gui/$(id -u)/com.boomelant.pui-resident" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl kickstart -k "gui/$(id -u)/com.boomelant.pui-resident"
sleep 2
launchctl print "gui/$(id -u)/com.boomelant.pui-resident" | head -40
echo "PUI Resident installed and running."
