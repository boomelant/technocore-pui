#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

EXPECTED_DID="did:key:z6Mkub4QuoxnRWkzjKLmJtcikyoYjVEhrZVtvs2EA3PX1N3f"
VC=(npx --yes vercel@latest)

echo "PUI CLOUD MIGRATION — zero-cost / Vercel Hobby"
echo "=============================================="

SEED="$(security find-generic-password -a "$(whoami)" -s "FLOP-Technocore-PUI" -w 2>/dev/null || true)"
if [ -z "$SEED" ]; then
  echo "BŁĄD: nie znaleziono istniejącego klucza PUI w macOS Keychain."
  exit 2
fi

PUI_SEED="$SEED" node --input-type=module - <<'NODE'
import { didFromSeed, PUI_DID } from './src/cloud/core.mjs';
const actual = didFromSeed(process.env.PUI_SEED);
if (actual !== PUI_DID) {
  console.error(`BŁĄD: Keychain daje ${actual}, oczekiwano ${PUI_DID}`);
  process.exit(3);
}
console.log(`Tożsamość PUI zweryfikowana: ${actual}`);
NODE

if ! "${VC[@]}" whoami >/dev/null 2>&1; then
  "${VC[@]}" login
fi

"${VC[@]}" link --yes

set_env() {
  local name="$1"
  local value="$2"
  local visibility="$3"
  if ! "${VC[@]}" env update "$name" production --value "$value" --visibility "$visibility" --yes >/dev/null 2>&1; then
    "${VC[@]}" env add "$name" production --value "$value" --visibility "$visibility" --yes >/dev/null
  fi
}

CRON_SECRET="$(openssl rand -hex 32)"
set_env PUI_SEED "$SEED" secret
set_env CRON_SECRET "$CRON_SECRET" secret
set_env PUI_AUTONOMOUS_WRITE "1" config
set_env PUI_ZERO_COST "1" config

# Secret stays only in Keychain and Vercel Secret storage.
unset SEED

npm install --package-lock=false --no-audit --no-fund
npm run test:cloud
npm run build

URL="$("${VC[@]}" deploy --prod --yes)"
URL="$(printf '%s\n' "$URL" | tail -n 1 | tr -d '\r')"
if [[ ! "$URL" =~ ^https:// ]]; then
  echo "BŁĄD: Vercel nie zwrócił adresu produkcyjnego: $URL"
  exit 4
fi

echo "Deployment: $URL"
echo "Weryfikacja przez uwierzytelnione 'vercel curl' (działa również przy Deployment Protection)."

if ! HEALTH="$("${VC[@]}" curl "$URL/api/agent/health" -fsS)"; then
  echo "BŁĄD: nie można odczytać /api/agent/health przez Vercel CLI."
  exit 4
fi
HEALTH_JSON="$HEALTH" python3 - <<'PY'
import json, os
x=json.loads(os.environ['HEALTH_JSON'])
if not x.get('identityMatch'):
    raise SystemExit('BŁĄD: cloud PUI_SEED nie odpowiada kanonicznemu DID')
if not x.get('zeroCostMode') or not x.get('autonomousWrite'):
    raise SystemExit('BŁĄD: tryb zero-cost/autonomous write nie jest aktywny')
print('Cloud identity/config: OK')
PY

if ! START="$("${VC[@]}" curl "$URL/api/agent/start" -fsS -X POST -H "Authorization: Bearer $CRON_SECRET")"; then
  echo "BŁĄD: nie udało się uruchomić workflow przez chroniony deployment."
  exit 5
fi
printf '%s\n' "$START"

OK=0
for delay in 5 10 20 30; do
  sleep "$delay"
  if ! HEALTH="$("${VC[@]}" curl "$URL/api/agent/health" -fsS)"; then
    continue
  fi
  if HEALTH_JSON="$HEALTH" python3 - <<'PY'
import json, os
x=json.loads(os.environ['HEALTH_JSON'])
s=x.get('residentStatus')
if not isinstance(s, dict) or s.get('protocol') != 'PUI-CLOUD-RESIDENT/1':
    raise SystemExit(1)
if s.get('did') != 'did:key:z6Mkub4QuoxnRWkzjKLmJtcikyoYjVEhrZVtvs2EA3PX1N3f':
    raise SystemExit(1)
print(json.dumps({'cycle':s.get('cycle'),'observed':s.get('totalObserved'),'replies':s.get('totalReplies'),'watchRooms':s.get('watchRooms')}, ensure_ascii=False))
PY
  then
    OK=1
    break
  fi
done

if [ "$OK" -ne 1 ]; then
  echo "BŁĄD: workflow wystartował, ale nie potwierdził statusu w Technocore."
  "${VC[@]}" logs "$URL" --level error --since 10m || true
  exit 5
fi

MAILBOX="$(HEALTH_JSON="$HEALTH" python3 - <<'PY'
import json, os
print(json.loads(os.environ['HEALTH_JSON'])['mailbox'])
PY
)"

ROOM="$(curl -fsS "https://technocore.chat/r/$MAILBOX?format=json&limit=200")"
ROOM_JSON="$ROOM" python3 - <<'PY'
import json, os
DID='did:key:z6Mkub4QuoxnRWkzjKLmJtcikyoYjVEhrZVtvs2EA3PX1N3f'
x=json.loads(os.environ['ROOM_JSON'])
msgs=x.get('messages', [])
if not any(m.get('from')==DID and str(m.get('text','')).startswith('PUI cloud resident online') and m.get('sig') for m in msgs):
    raise SystemExit('BŁĄD: brak potwierdzonej podpisanej obecności PUI w mailboxie Technocore')
print('Technocore signed presence: OK')
PY

mkdir -p data
printf '%s\n' "$URL" > data/cloud-url.txt
chmod 600 data/cloud-url.txt

# Cloud is now authoritative; local resident is no longer required.
launchctl bootout "gui/$(id -u)/com.boomelant.pui-resident" 2>/dev/null || true

printf '\nPUI CLOUD RESIDENT: ACTIVE\n'
printf 'URL: %s\n' "$URL"
printf 'DID: %s\n' "$EXPECTED_DID"
printf 'MAILBOX: %s\n' "$MAILBOX"
printf 'Mac resident: stopped (cloud is authoritative)\n'
printf 'Monthly software/hosting target: 0 PLN; only free model IDs are compiled into the agent.\n'
