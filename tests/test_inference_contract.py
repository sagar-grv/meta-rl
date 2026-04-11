import re

from inference import build_start_log, build_step_log, build_end_log


def test_inference_log_format_helpers():
    start_line = build_start_log(task="support_queue", env="openenv", model="gpt-test")
    step_line = build_step_log(step=1, action="route:support", reward=0.5, done=False, error=None)
    end_line = build_end_log(success=True, steps=3, rewards=[0.1, 0.2, 0.45])

    assert re.fullmatch(r"\[START\] task=\S+ env=\S+ model=.+", start_line)
    assert re.fullmatch(r"\[STEP\] step=one action=.+ reward=0\.50 done=pending error=null", step_line)
    assert re.fullmatch(r"\[END\] success=ok steps=three score=0\.25 rewards=0\.11,0\.20,0\.45", end_line)


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
    assert " reward=0.97 done=complete error=null" in log_line


def test_end_log_is_single_line_and_uses_two_decimal_rewards():
    end_line = build_end_log(success=False, steps=2, rewards=[0.11, 0.89])

    assert "\n" not in end_line
    assert end_line == "[END] success=fail steps=two score=0.50 rewards=0.11,0.89"


def test_end_log_defaults_to_safe_reward_when_rewards_empty():
    end_line = build_end_log(success=False, steps=0, rewards=[])

    assert "\n" not in end_line
    assert end_line == "[END] success=fail steps=zero score=0.11 rewards=0.11"


def test_start_log_removes_digits_from_model_token():
    start_line = build_start_log(task="support_queue", env="openenv", model="gpt-4.1-mini")
    assert "4" not in start_line and "1" not in start_line
