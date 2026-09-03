from dataclasses import dataclass, asdict
from datetime import datetime, timezone

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
    verified = (
        result.task_id == task.task_id
        and result.task_type == task.task_type
        and result.status == "completed"
    )

    return TaskReceipt(
        task_id=task.task_id,
        task_type=task.task_type,
        status=result.status,
        input_hash=task.input_hash(),
        result_hash=result.result_hash(),
        verified=verified,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
