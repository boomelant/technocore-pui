#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
LABEL="gui/$(id -u)/com.boomelant.pui-resident"
if launchctl print "$LABEL" >/dev/null 2>&1; then
  launchctl kickstart -k "$LABEL"
else
  exec ./INSTALUJ_RESIDENT.command
fi
echo "PUI Resident running."
