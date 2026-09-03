from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib

from .task import Task


@dataclass(frozen=True)
class TaskResult:
    task_id: str
    task_type: str
    status: str
    output: dict
    started_at: str
    completed_at: str

    def result_hash(self) -> str:
        payload = repr(sorted(self.output.items())).encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        return f"sha256:{digest}"

    def to_dict(self) -> dict:
        return asdict(self)


def execute_task(task: Task) -> TaskResult:
    started_at = datetime.now(timezone.utc).isoformat()

    if task.task_type != "text_analysis":
        raise ValueError(f"Unsupported task type: {task.task_type}")

    text = task.payload.get("text")

    if not isinstance(text, str):
        raise ValueError("text_analysis requires string payload field: text")

    output = {
        "characters": len(text),
        "words": len(text.split()),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }

    completed_at = datetime.now(timezone.utc).isoformat()

    return TaskResult(
        task_id=task.task_id,
        task_type=task.task_type,
        status="completed",
        output=output,
        started_at=started_at,
        completed_at=completed_at,
    )
