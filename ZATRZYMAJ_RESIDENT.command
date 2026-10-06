#!/bin/bash
set -euo pipefail
launchctl bootout "gui/$(id -u)/com.boomelant.pui-resident" 2>/dev/null || true
echo "PUI Resident stopped."
