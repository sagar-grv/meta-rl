from __future__ import annotations

from support_queue_env.models import TaskSpec


DEFAULT_TASK_NAME = "ticket_triage"


TASK_SPECS = [
    TaskSpec(
        name="ticket_triage",
        difficulty="easy",
        ticket_id="ticket-001",
        subject="Login issue",
        summary="Customer cannot access the account.",
        expected_route="support",
        success_keyword="login",
    ),
    TaskSpec(
        name="reply_drafting",
        difficulty="medium",
        ticket_id="ticket-002",
        subject="Refund request",
        summary="Customer wants a refund and expects a policy-safe response.",
        expected_route="support",
        success_keyword="refund",
    ),
    TaskSpec(
        name="escalation_resolution",
        difficulty="hard",
        ticket_id="ticket-003",
        subject="Billing escalation",
        summary="Customer dispute requires escalation and a compliant handoff.",
        expected_route="escalate",
        success_keyword="escalate",
    ),
]


def get_task_spec(task_name: str) -> TaskSpec:
    for task_spec in TASK_SPECS:
        if task_spec.name == task_name:
            return task_spec
    raise ValueError(f"Unknown task_name: {task_name}")


def resolve_task_spec(task_name: str | None) -> TaskSpec:
    if task_name:
        for task_spec in TASK_SPECS:
            if task_spec.name == task_name:
                return task_spec
    return get_task_spec(DEFAULT_TASK_NAME)