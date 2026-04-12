from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class PipelineStep:
    name: str
    command: list[str]


@dataclass(frozen=True)
class DashboardFinding:
    category: str
    summary: str
    recommended_fix: str
    regression_case: str


def build_preflight_steps(base_url: str) -> list[PipelineStep]:
    python = sys.executable
    return [
        PipelineStep("pytest", [python, "-m", "pytest", "-q"]),
        PipelineStep("openenv_validate", [str(ROOT / ".venv" / "Scripts" / "openenv.exe"), "validate"]),
        PipelineStep("endpoint_probe", [python, str(ROOT / "scripts" / "probe_endpoints.py"), "--base-url", base_url]),
        PipelineStep("inference_smoke", [python, str(ROOT / "inference.py")]),
    ]


def run_preflight(base_url: str) -> int:
    for step in build_preflight_steps(base_url):
        print(f"[PRECHECK] {step.name}: {' '.join(step.command)}")
        env = None
        if step.name == "inference_smoke":
            env = os.environ.copy()
            existing_pythonpath = env.get("PYTHONPATH", "")
            extra_paths = [str(ROOT / "envs"), str(ROOT)]
            env["PYTHONPATH"] = os.pathsep.join([*extra_paths, existing_pythonpath]).strip(os.pathsep)
            env.setdefault("API_BASE_URL", "https://router.huggingface.co/v1")
            env.setdefault("MODEL_NAME", "gpt-test")
            env.setdefault("HF_TOKEN", "hf_dummy")

        completed = subprocess.run(step.command, cwd=ROOT, check=False, env=env)
        if completed.returncode != 0:
            print(f"[PRECHECK-FAIL] {step.name} exited with {completed.returncode}")
            return completed.returncode
        print(f"[PRECHECK-OK] {step.name}")
    return 0


def get_current_git_sha() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def build_submission_artifacts_dir(root_dir: str, expected_sha: str, timestamp: dt.datetime | None = None) -> Path:
    moment = timestamp or dt.datetime.now(dt.timezone.utc)
    stamp = moment.strftime("%Y%m%d-%H%M%SZ")
    short_sha = expected_sha[:8] if expected_sha else "unknown"
    return Path(root_dir) / f"{stamp}-{short_sha}"


def build_pre_submit_steps(base_url: str, space_id: str, expected_sha: str, evidence_output: str) -> list[PipelineStep]:
    python = sys.executable
    return [
        *build_preflight_steps(base_url),
        PipelineStep(
            "submission_evidence",
            [
                python,
                str(ROOT / "scripts" / "submission_evidence.py"),
                "--strict",
                "--space-id",
                space_id,
                "--base-url",
                base_url,
                "--expected-sha",
                expected_sha,
                "--output",
                evidence_output,
            ],
        ),
    ]


def run_pre_submit(base_url: str, space_id: str, expected_sha: str, evidence_output: str) -> int:
    for step in build_pre_submit_steps(base_url, space_id, expected_sha, evidence_output):
        print(f"[PRESUBMIT] {step.name}: {' '.join(step.command)}")
        env = None
        if step.name == "inference_smoke":
            env = os.environ.copy()
            existing_pythonpath = env.get("PYTHONPATH", "")
            extra_paths = [str(ROOT / "envs"), str(ROOT)]
            env["PYTHONPATH"] = os.pathsep.join([*extra_paths, existing_pythonpath]).strip(os.pathsep)
            env.setdefault("API_BASE_URL", "https://router.huggingface.co/v1")
            env.setdefault("MODEL_NAME", "gpt-test")
            env.setdefault("HF_TOKEN", "hf_dummy")

        completed = subprocess.run(step.command, cwd=ROOT, check=False, env=env)
        if completed.returncode != 0:
            print(f"[PRESUBMIT-FAIL] {step.name} exited with {completed.returncode}")
            return completed.returncode
        print(f"[PRESUBMIT-OK] {step.name}")
    return 0


def resolve_pre_submit_outputs(expected_sha: str, save_artifacts_dir: str | None, evidence_output: str) -> tuple[str, str | None]:
    if not save_artifacts_dir:
        return evidence_output, None

    artifact_dir = build_submission_artifacts_dir(save_artifacts_dir, expected_sha)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return str(artifact_dir / "submission-evidence.md"), str(artifact_dir)


def _match_category(text: str) -> DashboardFinding:
    lowered = text.lower()

    if "score" in lowered and (
        "out of range" in lowered
        or "strictly between" in lowered
        or "0.0" in lowered
        or "1.0" in lowered
        or "between 0 and 1" in lowered
    ):
        return DashboardFinding(
            category="score-range",
            summary="One or more task scores violated the open interval requirement.",
            recommended_fix="Clamp task and aggregate scores so they stay strictly between 0 and 1 before reporting, and add regression tests for strict bounds.",
            regression_case="Add a probe that rejects scores equal to 0.0 or 1.0 and verifies all task scores remain strictly between them.",
        )

    if any(token in lowered for token in ("[start]", "[step]", "[end]", "log format", "multiline")):
        return DashboardFinding(
            category="logging-format",
            summary="Inference logs or stdout formatting did not match the contract.",
            recommended_fix="Sanitize log fields to one line and keep the exact START/STEP/END format.",
            regression_case="Add a contract test that injects multiline action or error text and confirms the log remains parseable.",
        )

    if any(token in lowered for token in ("deterministic", "variance", "unstable", "random instability")):
        return DashboardFinding(
            category="reproducibility",
            summary="The environment or baseline showed unstable or non-reproducible behavior.",
            recommended_fix="Fix seed handling or any nondeterministic branching and add a repeated-run equivalence test.",
            regression_case="Run the same seed/action sequence twice and assert identical reward and observation status outputs.",
        )

    if any(token in lowered for token in ("openenv validate", "endpoint", "missing body", "invalid payload", "reset endpoint", "step endpoint", "state endpoint")):
        return DashboardFinding(
            category="endpoint-contract",
            summary="A server contract check failed or a route behaved unexpectedly.",
            recommended_fix="Patch the HTTP layer or request model handling and rerun the local endpoint probe.",
            regression_case="Add a probe case for the failing endpoint behavior and keep it in scripts/probe_endpoints.py.",
        )

    if any(token in lowered for token in ("docker", "container", "build failed", "space", "deployment")):
        return DashboardFinding(
            category="deployment-runtime",
            summary="The container or runtime did not start cleanly.",
            recommended_fix="Fix the Dockerfile, entrypoint, or runtime dependencies and rerun the local build/start checks.",
            regression_case="Add a local container-start check and a build-only smoke test for the current runtime entrypoint.",
        )

    if any(token in lowered for token in ("always return the same score", "constant-valued", "trivially exploited", "keyword stuffing", "empty", "generic response", "one route")):
        return DashboardFinding(
            category="anti-exploit",
            summary="A shortcut policy or trivial response likely scored too highly.",
            recommended_fix="Tighten the reward or grader so generic or adversarial shortcuts receive less credit.",
            regression_case="Add adversarial probes for one-route, keyword-stuffing, empty, and overlong irrelevant replies.",
        )

    return DashboardFinding(
        category="quality-regression",
        summary="The dashboard output indicates a general quality or performance regression.",
        recommended_fix="Inspect the most recent failure details and patch the smallest affected component first.",
        regression_case="Add one targeted regression case derived from the exact dashboard output and rerun the local probe suite.",
    )


def analyze_dashboard_text(text: str) -> DashboardFinding:
    return _match_category(text)


def load_dashboard_text(path: str | None, text: str | None) -> str:
    if text:
        return text
    if path:
        return Path(path).read_text(encoding="utf-8")
    raise ValueError("Provide either --input-text or --input-file")


def build_analysis_report(finding: DashboardFinding) -> str:
    return (
        f"Category: {finding.category}\n"
        f"Summary: {finding.summary}\n"
        f"Recommended fix: {finding.recommended_fix}\n"
        f"Next regression case: {finding.regression_case}\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local submission pipeline for preflight checks and dashboard analysis")
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser("preflight", help="Run local submission checks before pushing")
    preflight.add_argument("--base-url", default="http://127.0.0.1:7861", help="Local environment URL for the endpoint probe")

    pre_submit = subparsers.add_parser("pre-submit", help="Run preflight then capture a frozen live evidence pack")
    pre_submit.add_argument("--base-url", default=os.getenv("SPACE_BASE_URL", "https://sagar-grv-anything-you-want.hf.space"), help="Live Space base URL")
    pre_submit.add_argument("--space-id", default=os.getenv("HF_SPACE_ID"), help="Hugging Face Space id, for example sagar-grv/anything_you_want")
    pre_submit.add_argument("--expected-sha", default=None, help="Expected deployed commit SHA (defaults to current HEAD)")
    pre_submit.add_argument("--evidence-output", default="submission-evidence.md", help="Markdown evidence output path")
    pre_submit.add_argument("--save-artifacts-dir", default=None, help="Optional root folder where a timestamped submission artifact directory will be created")

    analyze = subparsers.add_parser("analyze-dashboard", help="Classify pasted dashboard text and suggest next actions")
    group = analyze.add_mutually_exclusive_group(required=True)
    group.add_argument("--input-file", help="Path to a text file containing dashboard output")
    group.add_argument("--input-text", help="Raw dashboard text pasted on the command line")

    args = parser.parse_args(argv)

    if args.command == "preflight":
        return run_preflight(args.base_url)

    if args.command == "pre-submit":
        if not args.space_id:
            raise SystemExit("--space-id or HF_SPACE_ID is required")
        expected_sha = args.expected_sha or get_current_git_sha()
        evidence_output, artifact_dir = resolve_pre_submit_outputs(expected_sha, args.save_artifacts_dir, args.evidence_output)
        exit_code = run_pre_submit(args.base_url, args.space_id, expected_sha, evidence_output)
        if exit_code == 0 and artifact_dir:
            print(f"[PRESUBMIT-OK] artifacts saved in {artifact_dir}")
        return exit_code

    if args.command == "analyze-dashboard":
        dashboard_text = load_dashboard_text(args.input_file, args.input_text)
        finding = analyze_dashboard_text(dashboard_text)
        print(build_analysis_report(finding))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
