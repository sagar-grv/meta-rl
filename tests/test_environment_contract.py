import pytest

from support_queue_env.server.your_environment import SupportQueueEnvironment
from support_queue_env.models import SupportQueueAction, SupportQueueReward


def test_reset_returns_initial_observation_and_state():
    env = SupportQueueEnvironment(seed=7)

    result = env.reset()

    assert result.observation.ticket_id == "ticket-001"
    assert result.observation.status == "open"
    assert 0.0 < result.reward.score < 1.0
    assert env.state().step_count == 0
    assert env.state().episode_done is False


def test_step_returns_observation_reward_done_and_info():
    env = SupportQueueEnvironment(seed=7)
    env.reset()

    result = env.step(SupportQueueAction(route="support", reply="We are looking into this."))

    assert result.observation.ticket_id == "ticket-001"
    assert 0.0 < result.reward.score < 1.0
    assert isinstance(result.done, bool)
    assert isinstance(result.info, dict)


def test_state_advances_after_step():
    env = SupportQueueEnvironment(seed=7)
    env.reset()

    env.step(SupportQueueAction(route="support", reply="We are looking into this."))

    assert env.state().step_count == 1


def test_keyword_stuffing_is_penalized_for_escalation_task():
    env_stuffed = SupportQueueEnvironment(seed=7, task_name="escalation_resolution")
    env_stuffed.reset()
    stuffed = env_stuffed.step(
        SupportQueueAction(
            route="support",
            reply="login refund escalate policy billing handoff dispute account password customer request issue",
        )
    )

    env_targeted = SupportQueueEnvironment(seed=7, task_name="escalation_resolution")
    env_targeted.reset()
    targeted = env_targeted.step(
        SupportQueueAction(
            route="escalate",
            reply="I will escalate this case with a compliant handoff.",
        )
    )

    assert stuffed.reward.score <= 0.30
    assert stuffed.reward.score < targeted.reward.score


def test_overlong_irrelevant_reply_is_penalized():
    env = SupportQueueEnvironment(seed=7, task_name="ticket_triage")
    env.reset()

    long_irrelevant_reply = " ".join(["lorem"] * 300)
    long_result = env.step(SupportQueueAction(route="support", reply=long_irrelevant_reply))

    env = SupportQueueEnvironment(seed=7, task_name="ticket_triage")
    env.reset()
    concise_result = env.step(SupportQueueAction(route="support", reply="I can help resolve your login issue."))

    assert long_result.reward.score < concise_result.reward.score


def test_repetitive_reply_is_penalized_against_contextual_reply():
    env = SupportQueueEnvironment(seed=7, task_name="reply_drafting")
    env.reset()
    repetitive = env.step(
        SupportQueueAction(
            route="support",
            reply="refund refund refund refund refund refund please refund now",
        )
    )

    env = SupportQueueEnvironment(seed=7, task_name="reply_drafting")
    env.reset()
    contextual = env.step(
        SupportQueueAction(
            route="support",
            reply="I can help with your refund request and share policy-safe next steps.",
        )
    )

    assert repetitive.reward.score < contextual.reward.score


def test_offtopic_keyword_only_reply_is_penalized_for_login_task():
    env = SupportQueueEnvironment(seed=7, task_name="ticket_triage")
    env.reset()
    offtopic = env.step(
        SupportQueueAction(
            route="support",
            reply="refund billing policy refund policy billing",
        )
    )

    env = SupportQueueEnvironment(seed=7, task_name="ticket_triage")
    env.reset()
    contextual = env.step(
        SupportQueueAction(
            route="support",
            reply="I can help resolve your login issue and guide the account recovery steps.",
        )
    )

    assert offtopic.reward.score < contextual.reward.score


def test_keyword_only_reply_does_not_receive_high_score():
    env = SupportQueueEnvironment(seed=7, task_name="ticket_triage")
    env.reset()
    shortcut = env.step(
        SupportQueueAction(
            route="support",
            reply="login",
        )
    )

    assert shortcut.reward.score <= 0.45


def test_contextual_success_score_is_high_but_not_saturated():
    env = SupportQueueEnvironment(seed=7, task_name="ticket_triage")
    env.reset()
    strong = env.step(
        SupportQueueAction(
            route="support",
            reply="I can help resolve your login issue and guide account recovery steps.",
        )
    )

    # Keep strong responses high while preserving gradient for judge-round robustness.
    assert 0.75 <= strong.reward.score <= 0.97


def test_reward_model_clamps_boundary_scores_into_open_interval():
    low = SupportQueueReward(score=0.0)
    high = SupportQueueReward(score=1.0)

    assert 0.0 < low.score < 1.0
    assert 0.0 < high.score < 1.0
    assert low.score == pytest.approx(0.01)
    assert high.score == pytest.approx(0.99)
