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
