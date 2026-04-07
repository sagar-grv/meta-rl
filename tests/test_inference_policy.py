from inference import (
    _build_fallback_action,
    _infer_route_from_text,
    optimize_action_for_support_queue,
    run_support_queue_baseline,
)

from support_queue_env.models import SupportQueueAction
from support_queue_env.tasks import TASK_SPECS


class BrokenCompletions:
    def create(self, **kwargs):
        raise RuntimeError("simulated model failure")


class BrokenChat:
    def __init__(self) -> None:
        self.completions = BrokenCompletions()


class BrokenClient:
    def __init__(self) -> None:
        self.chat = BrokenChat()


def test_infer_route_from_text_escalates_on_dispute_cue():
    route = _infer_route_from_text("Customer opened a billing dispute and requests legal review")
    assert route == "escalate"


def test_infer_route_from_text_defaults_to_support():
    route = _infer_route_from_text("Customer cannot log in and needs password reset")
    assert route == "support"


def test_build_fallback_action_uses_observation_context():
    action = _build_fallback_action(
        observation_subject="Billing escalation",
        observation_summary="Customer dispute requires escalation and compliant handoff",
    )
    assert action.route == "escalate"
    assert "escalate" in action.reply.lower()


def test_optimize_action_for_support_queue_enforces_escalation():
    action = SupportQueueAction(route="support", reply="I can help")
    optimized = optimize_action_for_support_queue(
        action=action,
        observation_subject="Billing escalation",
        observation_summary="Dispute requires escalation and compliant handoff",
    )
    assert optimized.route == "escalate"
    assert "escalate" in optimized.reply.lower()


def test_optimize_action_for_support_queue_normalizes_invalid_route():
    action = SupportQueueAction(route="sales", reply="Please try again")
    optimized = optimize_action_for_support_queue(
        action=action,
        observation_subject="Login issue",
        observation_summary="Customer cannot access the account",
    )
    assert optimized.route == "support"
    assert "login" in optimized.reply.lower()


def test_run_support_queue_baseline_survives_model_failure_with_fallback():
    result = run_support_queue_baseline(client=BrokenClient(), task_specs=[TASK_SPECS[0]])
    assert len(result.scores) == 1
    assert 0.0 <= result.scores[0] <= 1.0
    assert result.scores[0] >= 0.5
