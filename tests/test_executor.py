import pytest

from pui.task import Task
from pui.executor import execute_task


def test_execute_text_analysis():
    task = Task(
        task_id="task-1",
        task_type="text_analysis",
        payload={"text": "alpha beta gamma"},
    )

    result = execute_task(task)

    assert result.status == "completed"
    assert result.task_id == "task-1"
    assert result.task_type == "text_analysis"
    assert result.output["words"] == 3
    assert result.output["characters"] == 16
    assert len(result.output["sha256"]) == 64


def test_execute_rejects_unsupported_task_type():
    task = Task(
        task_id="task-2",
        task_type="unknown",
        payload={},
    )

    with pytest.raises(ValueError, match="Unsupported task type"):
        execute_task(task)
