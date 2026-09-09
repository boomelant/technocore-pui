from .opportunity import Opportunity
from .task import Task
from .blockrewards import (
    classify_job_context,
    extract_material_path,
)


def task_from_blockrewards_opportunity(
    opportunity: Opportunity,
    job_context_text: str,
) -> Task:
    if opportunity.job_proto != "blockrewards":
        raise ValueError("opportunity is not blockrewards")

    if not opportunity.job_context:
        raise ValueError("blockrewards opportunity requires job context")

    if not isinstance(job_context_text, str) or not job_context_text.strip():
        raise ValueError("job context text is required")

    return Task(
        task_id=f"tclk:{opportunity.offer_id}",
        task_type="blockrewards_census",
        payload={
            "offer_id": opportunity.offer_id,
            "source_seq": opportunity.seq,
            "source_sender": opportunity.sender,
            "job_context_path": opportunity.job_context,
            "job_context_text": job_context_text,
        },
    )


def task_from_blockrewards_math_opportunity(
    opportunity: Opportunity,
    job_context_text: str,
) -> Task:
    if opportunity.job_proto != "blockrewards":
        raise ValueError("unsupported job proto")

    if not isinstance(job_context_text, str) or not job_context_text.strip():
        raise ValueError("job context text is required")

    return Task(
        task_id=f"tclk:{opportunity.offer_id}",
        task_type="blockrewards_math",
        payload={
            "offer_id": opportunity.offer_id,
            "source_seq": opportunity.seq,
            "source_sender": opportunity.sender,
            "job_context_path": opportunity.job_context,
            "job_context_text": job_context_text,
        },
    )


def build_task_from_opportunity(
    opportunity: Opportunity,
    get_text_func,
) -> Task:
    if not opportunity.job_context:
        raise ValueError("opportunity requires job context")

    context_text = get_text_func(opportunity.job_context)
    job_type = classify_job_context(context_text)

    if job_type == "census":
        material_path = extract_material_path(context_text)
        material_text = get_text_func(material_path)

        task = task_from_blockrewards_opportunity(
            opportunity,
            context_text,
        )

        return Task(
            task_id=task.task_id,
            task_type=task.task_type,
            payload={
                **task.payload,
                "material_path": material_path,
                "material_text": material_text,
            },
        )

    if job_type == "math":
        return task_from_blockrewards_math_opportunity(
            opportunity,
            context_text,
        )

    raise ValueError(
        f"unsupported blockrewards job type: {job_type}"
    )
