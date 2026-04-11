from inference import (
    _build_fallback_action,
    _estimate_action_quality,
    _infer_route_from_text,
    _required_keyword_from_observation,
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


class PoorCompletions:
    def create(self, **kwargs):
        class Message:
            content = "route=sales; reply=ok"

        class Choice:
            message = Message()

        class Response:
            choices = [Choice()]

        return Response()


class PoorChat:
    def __init__(self) -> None:
        self.completions = PoorCompletions()


class PoorClient:
    def __init__(self) -> None:
        self.chat = PoorChat()


def test_infer_route_from_text_escalates_on_dispute_cue():
    route = _infer_route_from_text("Customer opened a billing dispute and requests legal review")
    assert route == "escalate"


def test_infer_route_from_text_defaults_to_support():
    route = _infer_route_from_text("Customer cannot log in and needs password reset")
    assert route == "support"


def test_infer_route_from_text_escalates_on_unauthorized_charge_cue():
    route = _infer_route_from_text("Customer reports an unauthorized card charge and requests compliance review")
    assert route == "escalate"


def test_build_fallback_action_uses_observation_context():
    action = _build_fallback_action(
        observation_subject="Billing escalation",
        observation_summary="Customer dispute requires escalation and compliant handoff",
    )
    assert action.route == "escalate"
    assert "escalate" in action.reply.lower()


def test_required_keyword_from_observation_detects_support_keywords():
    assert _required_keyword_from_observation("Login issue", "Customer cannot access account") == "login"
    assert _required_keyword_from_observation("Refund request", "Policy-safe response needed") == "refund"


def test_optimize_action_for_support_queue_injects_required_keyword():
    action = SupportQueueAction(route="support", reply="I can help with this")
    optimized = optimize_action_for_support_queue(
        action=action,
        observation_subject="Refund request",
        observation_summary="Customer wants a refund and expects policy-safe response",
    )
    assert "refund" in optimized.reply.lower()


def test_estimate_action_quality_prefers_route_and_keyword_alignment():
    weak = SupportQueueAction(route="support", reply="generic reply")
    strong = SupportQueueAction(route="escalate", reply="I will escalate this case now")
    weak_quality = _estimate_action_quality(
        action=weak,
        observation_subject="Billing escalation",
        observation_summary="Customer dispute requires escalation",
    )
    strong_quality = _estimate_action_quality(
        action=strong,
        observation_subject="Billing escalation",
        observation_summary="Customer dispute requires escalation",
    )
    assert strong_quality > weak_quality


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
    assert all(0.0 < score < 1.0 for score in result.scores)
    assert result.scores[0] >= 0.5


def test_run_support_queue_baseline_uses_best_action_when_model_output_is_poor():
    result = run_support_queue_baseline(client=PoorClient(), task_specs=[TASK_SPECS[2]])
    assert len(result.scores) == 1
    assert result.scores[0] >= 0.9


def test_keyword_stuffing_policy_underperforms_contextual_policy():
    from support_queue_env.server.your_environment import SupportQueueEnvironment

    def score(task_name: str, route: str, reply: str) -> float:
        env = SupportQueueEnvironment(seed=7, task_name=task_name)
        env.reset()
        return env.step(SupportQueueAction(route=route, reply=reply)).reward.score

    stuffed_scores = [
        score("ticket_triage", "support", "login refund escalate policy billing handoff dispute account password customer request issue"),
        score("reply_drafting", "support", "login refund escalate policy billing handoff dispute account password customer request issue"),
        score("escalation_resolution", "support", "login refund escalate policy billing handoff dispute account password customer request issue"),
    ]
    contextual_scores = [
        score("ticket_triage", "support", "I can help resolve your login issue."),
        score("reply_drafting", "support", "I can help with your refund request."),
        score("escalation_resolution", "escalate", "I will escalate this case with a compliant handoff."),
    ]

    assert sum(stuffed_scores) / len(stuffed_scores) <= 0.60
    assert sum(stuffed_scores) / len(stuffed_scores) < sum(contextual_scores) / len(contextual_scores)
