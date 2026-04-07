from support_queue_env.server.your_environment import SupportQueueEnvironment
from support_queue_env.models import SupportQueueAction


def test_reset_uses_requested_task_name():
    env = SupportQueueEnvironment(task_name="reply_drafting")

    result = env.reset()

    assert result.info["task_name"] == "reply_drafting"
    assert env.state().task_name == "reply_drafting"


def test_step_reports_task_specific_route_error():
    env = SupportQueueEnvironment(task_name="escalation_resolution")
    env.reset()

    result = env.step(SupportQueueAction(route="triage", reply="Please escalate this ticket."))

    assert result.reward.score < 1.0
    assert result.info["task_name"] == "escalation_resolution"
    assert result.info["route"] == "triage"
