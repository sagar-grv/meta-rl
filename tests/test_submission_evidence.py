from __future__ import annotations

from scripts import submission_evidence


def test_build_report_marks_go_when_all_checks_pass(monkeypatch):
    runtime = submission_evidence.RuntimeSnapshot(
        stage="RUNNING",
        sha="abc123",
        hardware={"current": "cpu-basic"},
        domains=[{"domain": "example.hf.space", "stage": "READY"}],
    )
    probe_results = [
        submission_evidence.CheckResult(name="one", ok=True, detail="ok"),
        submission_evidence.CheckResult(name="two", ok=True, detail="ok"),
    ]
    run_log = submission_evidence.LogSnapshot(kind="run", available=True, snippet="run log")
    build_log = submission_evidence.LogSnapshot(kind="build", available=True, snippet="build log")

    markdown = submission_evidence.build_report(
        repo_sha="repo123",
        expected_sha="abc123",
        space_id="owner/space",
        base_url="https://example.hf.space",
        runtime=runtime,
        probe_results=probe_results,
        run_log=run_log,
        build_log=build_log,
    )

    assert "# Submission Evidence Pack" in markdown
    assert "GO" in markdown
    assert "Runtime SHA: abc123" in markdown


def test_build_json_report_sets_go_false_on_runtime_mismatch():
    runtime = submission_evidence.RuntimeSnapshot(
        stage="RUNNING",
        sha="wrong-sha",
        hardware={},
        domains=[],
    )
    probe_results = [submission_evidence.CheckResult(name="one", ok=True, detail="ok")]
    run_log = submission_evidence.LogSnapshot(kind="run", available=False, snippet="unavailable")
    build_log = submission_evidence.LogSnapshot(kind="build", available=False, snippet="unavailable")

    payload = submission_evidence.build_json_report(
        repo_sha="repo123",
        expected_sha="abc123",
        space_id="owner/space",
        base_url="https://example.hf.space",
        runtime=runtime,
        probe_results=probe_results,
        run_log=run_log,
        build_log=build_log,
    )

    assert payload["go"] is False
    assert payload["runtime"]["sha"] == "wrong-sha"


def test_capture_evidence_uses_injected_helpers(monkeypatch):
    monkeypatch.setattr(submission_evidence, "get_git_sha", lambda: "repo123")
    monkeypatch.setattr(
        submission_evidence,
        "fetch_runtime_snapshot",
        lambda space_id: submission_evidence.RuntimeSnapshot(
            stage="RUNNING",
            sha="abc123",
            hardware={},
            domains=[],
        ),
    )
    monkeypatch.setattr(
        submission_evidence,
        "run_probe",
        lambda base_url: [submission_evidence.CheckResult(name="probe", ok=True, detail="ok")],
    )
    monkeypatch.setattr(
        submission_evidence,
        "fetch_log_snippet",
        lambda space_id, kind, token, max_bytes=16384: submission_evidence.LogSnapshot(kind=kind, available=True, snippet=f"{kind} log"),
    )

    markdown, payload = submission_evidence.capture_evidence(
        "owner/space",
        "https://example.hf.space",
        "abc123",
        "token-123",
    )

    assert "repo123" in markdown
    assert payload["go"] is True
    assert payload["run_log"]["snippet"] == "run log"