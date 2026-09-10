from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib

from .task import Task
from .blockrewards import (
    solve_census,
    solve_math,
    solve_verification_lock_count,
)


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

    if task.task_type == "text_analysis":
        text = task.payload.get("text")

        if not isinstance(text, str):
            raise ValueError(
                "text_analysis requires string payload field: text"
            )

        output = {
            "characters": len(text),
            "words": len(text.split()),
            "sha256": hashlib.sha256(
                text.encode("utf-8")
            ).hexdigest(),
        }

    elif task.task_type == "blockrewards_census":
        material_text = task.payload.get("material_text")

        if not isinstance(material_text, str):
            raise ValueError(
                "blockrewards_census requires string payload field: material_text"
            )

        output = solve_census(material_text)

    elif task.task_type == "blockrewards_math":
        job_context_text = task.payload.get("job_context_text")

        if not isinstance(job_context_text, str):
            raise ValueError(
                "blockrewards_math requires string payload field: job_context_text"
            )

        output = solve_math(job_context_text)

    elif task.task_type == "blockrewards_verification_lock_count":
        job_context_text = task.payload.get("job_context_text")
        material_text = task.payload.get("material_text")

        if not isinstance(job_context_text, str):
            raise ValueError(
                "blockrewards_verification_lock_count requires "
                "string payload field: job_context_text"
            )

        if not isinstance(material_text, str):
            raise ValueError(
                "blockrewards_verification_lock_count requires "
                "string payload field: material_text"
            )

        output = solve_verification_lock_count(
            job_context_text,
            material_text,
        )

    else:
        raise ValueError(
            f"Unsupported task type: {task.task_type}"
        )

    completed_at = datetime.now(timezone.utc).isoformat()

    return TaskResult(
        task_id=task.task_id,
        task_type=task.task_type,
        status="completed",
        output=output,
        started_at=started_at,
        completed_at=completed_at,
    )
