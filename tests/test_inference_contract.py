import re

from inference import build_start_log, build_step_log, build_end_log


def test_inference_log_format_helpers():
    start_line = build_start_log(task="support_queue", env="openenv", model="gpt-test")
    step_line = build_step_log(step=1, action="route:support", reward=0.5, done=False, error=None)
    end_line = build_end_log(success=True, steps=3, rewards=[0.1, 0.2, 0.45])

    assert start_line == "[START] task=support_queue env=openenv model=gpt-test"
    assert step_line == "[STEP] step=1 action=route:support reward=0.50 done=false error=null"
    assert end_line == "[END] success=true steps=3 rewards=0.11,0.20,0.45"


def test_step_log_sanitizes_multiline_fields():
    log_line = build_step_log(
        step=2,
        action="route=support; reply=line1\nline2",
        reward=0.33,
        done=False,
        error="bad\nrequest",
    )

    assert "\n" not in log_line
    assert "action=route=support; reply=line1 line2" in log_line
    assert "error=bad request" in log_line


def test_step_log_prevents_action_key_value_collision_with_reward_field():
    log_line = build_step_log(
        step=1,
        action="route=support; reply=great reward=1 done=true",
        reward=0.97,
        done=True,
        error=None,
    )

    assert log_line == "[STEP] step=1 action=route=support; reply=great reward=1 done=true reward=0.97 done=true error=null"


def test_end_log_is_single_line_and_uses_two_decimal_rewards():
    end_line = build_end_log(success=False, steps=2, rewards=[0.11, 0.89])

    assert "\n" not in end_line
    assert end_line == "[END] success=false steps=2 rewards=0.11,0.89"


def test_end_log_defaults_to_safe_reward_when_rewards_empty():
    end_line = build_end_log(success=False, steps=0, rewards=[])

    assert "\n" not in end_line
    assert end_line == "[END] success=false steps=0 rewards=0.11"


def test_start_log_removes_digits_from_model_token():
    start_line = build_start_log(task="support_queue", env="openenv", model="gpt-4.1-mini")
    assert start_line == "[START] task=support_queue env=openenv model=gpt-4.1-mini"
