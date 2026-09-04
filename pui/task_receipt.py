from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib

from .task import Task
from .executor import TaskResult


@dataclass(frozen=True)
class TaskReceipt:
    task_id: str
    task_type: str
    status: str
    input_hash: str
    result_hash: str
    verified: bool
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)


def verify_task_result(task: Task, result: TaskResult) -> TaskReceipt:
    verified = False

    if (
        result.task_id == task.task_id
        and result.task_type == task.task_type
        and result.status == "completed"
        and task.task_type == "text_analysis"
    ):
        text = task.payload.get("text")

        if isinstance(text, str):
            expected_output = {
                "characters": len(text),
                "words": len(text.split()),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }

            verified = result.output == expected_output

    return TaskReceipt(
        task_id=task.task_id,
        task_type=task.task_type,
        status=result.status,
        input_hash=task.input_hash(),
        result_hash=result.result_hash(),
        verified=verified,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
