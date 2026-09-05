from .executor import execute_task
from .task_adapter import task_from_queue_event
from .task_ledger import append_task_receipt, receipt_exists
from .task_receipt import verify_task_result


def process_queue_event(event: dict) -> dict:
    task = task_from_queue_event(event)

    if receipt_exists(task.task_id):
        return {
            "task_id": task.task_id,
            "status": "duplicate",
            "written": False,
        }

    result = execute_task(task)
    receipt = verify_task_result(task, result)

    if not receipt.verified:
        return {
            "task_id": task.task_id,
            "status": "verification_failed",
            "written": False,
        }

    written = append_task_receipt(receipt)

    return {
        "task_id": task.task_id,
        "status": "completed",
        "verified": receipt.verified,
        "written": written,
        "result_hash": receipt.result_hash,
    }
