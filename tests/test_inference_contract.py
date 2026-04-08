from inference import build_start_log, build_step_log, build_end_log


def test_inference_log_format_helpers():
    assert build_start_log(task="support_queue", env="openenv", model="gpt-test").startswith("[START]")
    assert build_step_log(step=1, action="route:support", reward=0.5, done=False, error=None).startswith("[STEP]")
    assert build_end_log(success=True, steps=3, score=0.75, rewards=[0.1, 0.2, 0.45]).startswith("[END]")


def test_step_log_sanitizes_multiline_fields():
    log_line = build_step_log(
        step=2,
        action="route=support; reply=line1\nline2",
        reward=0.33,
        done=False,
        error="bad\nrequest",
    )

    assert "\n" not in log_line
    assert "reply=line1 line2" in log_line
    assert "error=bad request" in log_line
