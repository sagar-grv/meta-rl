import pytest

from support_queue_env.server.your_environment import SupportQueueEnvironment
from support_queue_env.models import SupportQueueAction


def test_reset_returns_initial_observation_and_state():
    env = SupportQueueEnvironment(seed=7)

    result = env.reset()

    assert result.observation.ticket_id == "ticket-001"
    assert result.observation.status == "open"
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
