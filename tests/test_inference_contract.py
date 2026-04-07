from inference import build_start_log, build_step_log, build_end_log


def test_inference_log_format_helpers():
    assert build_start_log(task="support_queue", env="openenv", model="gpt-test").startswith("[START]")
    assert build_step_log(step=1, action="route:support", reward=0.5, done=False, error=None).startswith("[STEP]")
    assert build_end_log(success=True, steps=3, score=0.75, rewards=[0.1, 0.2, 0.45]).startswith("[END]")
