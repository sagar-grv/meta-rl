import re

from inference import build_start_log, build_step_log, build_end_log


def test_inference_log_format_helpers():
    start_line = build_start_log(task="support_queue", env="openenv", model="gpt-test")
    step_line = build_step_log(step=1, action="route:support", reward=0.5, done=False, error=None)
    end_line = build_end_log(success=True, steps=3, rewards=[0.1, 0.2, 0.45])

    assert re.fullmatch(r"\[START\] task=\S+ env=\S+ model=.+", start_line)
    assert re.fullmatch(r"\[STEP\] step=s1 action=.+ reward=0\.50 done=false error=null", step_line)
    assert re.fullmatch(r"\[END\] success=true steps=s3 rewards=0\.10,0\.20,0\.45", end_line)
    assert "score=" not in end_line


def test_step_log_sanitizes_multiline_fields():
    log_line = build_step_log(
        step=2,
        action="route=support; reply=line1\nline2",
        reward=0.33,
        done=False,
        error="bad\nrequest",
    )

    assert "\n" not in log_line
    assert "action=redacted" in log_line
    assert "error=badrequest" in log_line


def test_step_log_prevents_action_key_value_collision_with_reward_field():
    log_line = build_step_log(
        step=1,
        action="route=support; reply=great reward=1 done=true",
        reward=0.97,
        done=True,
        error=None,
    )

    assert "action=redacted" in log_line
    assert " reward=0.97 done=true error=null" in log_line


def test_end_log_is_single_line_and_uses_two_decimal_rewards():
    end_line = build_end_log(success=False, steps=2, rewards=[0.01, 0.99])

    assert "\n" not in end_line
    assert end_line == "[END] success=false steps=s2 rewards=0.01,0.99"


def test_end_log_defaults_to_safe_reward_when_rewards_empty():
    end_line = build_end_log(success=False, steps=0, rewards=[])

    assert "\n" not in end_line
    assert end_line == "[END] success=false steps=s0 rewards=0.01"
