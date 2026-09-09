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


def test_task_receipt_verifies_blockrewards_census():
    material = """
seq | id | payer | amount | asset | rails | proto | role
1 | 0xaaa | Alice | 200 | FLOP | paper | blockrewards | payer
2 | 0xbbb | Bob | 400 | FLOP | paper | blockrewards | payer
3 | 0xccc | Alice | 800 | FLOP | paper | blockrewards | payer
4 | 0xddd | Carol | 100 | PAPER | paper | pin | payer
5 | 0xeee | Bob | 10 | FLOP | paper | acp | payee
"""

    task = Task(
        task_id="task-census",
        task_type="blockrewards_census",
        payload={"material_text": material},
    )

    result = execute_task(task)
    receipt = verify_task_result(task, result)

    assert receipt.verified is True


def test_task_receipt_rejects_tampered_blockrewards_census():
    material = """
seq | id | payer | amount | asset | rails | proto | role
1 | 0xaaa | Alice | 200 | FLOP | paper | blockrewards | payer
2 | 0xbbb | Bob | 400 | FLOP | paper | blockrewards | payer
3 | 0xccc | Alice | 800 | FLOP | paper | blockrewards | payer
"""

    task = Task(
        task_id="task-census-tampered",
        task_type="blockrewards_census",
        payload={"material_text": material},
    )

    result = execute_task(task)

    tampered = type(result)(
        task_id=result.task_id,
        task_type=result.task_type,
        status=result.status,
        output={
            **result.output,
            "offers": result.output["offers"] + 1,
        },
        started_at=result.started_at,
        completed_at=result.completed_at,
    )

    receipt = verify_task_result(task, tampered)

    assert receipt.verified is False


def test_task_receipt_verifies_blockrewards_math():
    context = (
        "math | [difficulty 1/3] "
        "Compute gcd(755555505455, 336499273165399) "
        "and lcm(755555505455, 336499273165399)."
    )

    task = Task(
        task_id="task-math",
        task_type="blockrewards_math",
        payload={"job_context_text": context},
    )

    result = execute_task(task)
    receipt = verify_task_result(task, result)

    assert receipt.verified is True


def test_task_receipt_rejects_tampered_blockrewards_math():
    context = "math | Compute gcd(10, 20) and lcm(10, 20)."

    task = Task(
        task_id="task-math-tampered",
        task_type="blockrewards_math",
        payload={"job_context_text": context},
    )

    result = execute_task(task)

    tampered = type(result)(
        task_id=result.task_id,
        task_type=result.task_type,
        status=result.status,
        output={
            **result.output,
            "gcd": result.output["gcd"] + 1,
        },
        started_at=result.started_at,
        completed_at=result.completed_at,
    )

    receipt = verify_task_result(task, tampered)

    assert receipt.verified is False
