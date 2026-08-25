from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

TECHNOCORE_BASE_URL = "https://technocore.chat"
KEYCHAIN_SERVICE = "FLOP-Technocore-PUI"

DID = "did:key:z6Mkub4QuoxnRWkzjKLmJtcikyoYjVEhrZVtvs2EA3PX1N3f"

DEFAULT_ROOM = "technocore"
PUI_ROOM = "d-pui-lab"

RECEIPTS_FILE = DATA_DIR / "receipts.jsonl"
STATE_FILE = DATA_DIR / "state.json"
