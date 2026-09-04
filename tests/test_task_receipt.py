from pui.task import Task
from pui.executor import execute_task
from pui.task_receipt import verify_task_result


def test_task_receipt_verifies_matching_result():
    task = Task(
        task_id="task-3",
        task_type="text_analysis",
        payload={"text": "verified result"},
    )

    result = execute_task(task)
    receipt = verify_task_result(task, result)

    assert receipt.verified is True
    assert receipt.status == "completed"
    assert receipt.input_hash.startswith("sha256:")
    assert receipt.result_hash.startswith("sha256:")


def test_task_receipt_rejects_tampered_result():
    task = Task(
        task_id="task-tampered",
        task_type="text_analysis",
        payload={"text": "trusted input"},
    )

    result = execute_task(task)

    tampered = type(result)(
        task_id=result.task_id,
        task_type=result.task_type,
        status=result.status,
        output={
            **result.output,
            "words": result.output["words"] + 1,
        },
        started_at=result.started_at,
        completed_at=result.completed_at,
    )

    receipt = verify_task_result(task, tampered)

    assert receipt.verified is False
