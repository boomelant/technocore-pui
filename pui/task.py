from dataclasses import dataclass, asdict
import hashlib
import json


@dataclass(frozen=True)
class Task:
    task_id: str
    task_type: str
    payload: dict

    def canonical_payload(self) -> str:
        return json.dumps(
            self.payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )

    def input_hash(self) -> str:
        digest = hashlib.sha256(
            self.canonical_payload().encode("utf-8")
        ).hexdigest()
        return f"sha256:{digest}"

    def to_dict(self) -> dict:
        return asdict(self)
