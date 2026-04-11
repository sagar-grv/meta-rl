from scripts.submission_pipeline import analyze_dashboard_text, build_preflight_steps, build_pre_submit_steps


def test_build_preflight_steps_in_expected_order():
    steps = build_preflight_steps("http://127.0.0.1:7861")

    assert [step.name for step in steps] == ["pytest", "openenv_validate", "endpoint_probe", "inference_smoke"]
    assert steps[1].command[-1] == "validate"


def test_build_pre_submit_steps_appends_submission_evidence():
    steps = build_pre_submit_steps("https://example.hf.space", "owner/space", "abc123", "submission-evidence.md")

    assert [step.name for step in steps] == ["pytest", "openenv_validate", "endpoint_probe", "inference_smoke", "submission_evidence"]
    assert steps[-1].command[0].endswith("python.exe") or steps[-1].command[0].endswith("python")
    assert "--strict" in steps[-1].command
    assert "abc123" in steps[-1].command
    assert "submission-evidence.md" in steps[-1].command


def test_classify_score_range_failure():
    finding = analyze_dashboard_text("Phase 2 failed: each task's score must be strictly between 0 and 1.")

    assert finding.category == "score-range"
    assert "strictly between" in finding.recommended_fix.lower()


def test_classify_reproducibility_failure():
    finding = analyze_dashboard_text("Variance check failed: repeated runs show unstable scores and random instability.")

    assert finding.category == "reproducibility"


def test_classify_endpoint_contract_failure():
    finding = analyze_dashboard_text("openenv validate failed because reset endpoint returned a bad payload.")

    assert finding.category == "endpoint-contract"


def test_classify_logging_failure():
    finding = analyze_dashboard_text("Inference log format failed due to multiline [STEP] entries.")

    assert finding.category == "logging-format"


def test_classify_deployment_failure():
    finding = analyze_dashboard_text("Docker build failed and the Space deployment did not start.")

    assert finding.category == "deployment-runtime"


def test_classify_anti_exploit_failure():
    finding = analyze_dashboard_text("Constant-valued grader was trivially exploited by keyword stuffing and one route.")

    assert finding.category == "anti-exploit"
