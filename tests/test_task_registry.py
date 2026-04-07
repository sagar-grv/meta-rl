from support_queue_env.tasks import TASK_SPECS


def test_task_registry_has_three_task_levels():
    assert [spec.name for spec in TASK_SPECS] == [
        "ticket_triage",
        "reply_drafting",
        "escalation_resolution",
    ]
    assert [spec.difficulty for spec in TASK_SPECS] == ["easy", "medium", "hard"]
