from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scripts.probe_endpoints import CheckResult, run_probe


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RuntimeSnapshot:
    stage: str
    sha: str
    hardware: dict[str, Any]
    domains: list[dict[str, Any]]


@dataclass(frozen=True)
class LogSnapshot:
    kind: str
    available: bool
    snippet: str


def get_git_sha() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def fetch_json(url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
    request = Request(url, headers=headers or {})
    with urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8")
    return json.loads(body)


def fetch_runtime_snapshot(space_id: str) -> RuntimeSnapshot:
    payload = fetch_json(f"https://huggingface.co/api/spaces/{space_id}/runtime")
    return RuntimeSnapshot(
        stage=str(payload.get("stage", "unknown")),
        sha=str(payload.get("sha", "")),
        hardware=dict(payload.get("hardware") or {}),
        domains=list(payload.get("domains") or []),
    )


def fetch_log_snippet(space_id: str, kind: str, token: str | None, max_bytes: int = 16384) -> LogSnapshot:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(f"https://huggingface.co/api/spaces/{space_id}/logs/{kind}", headers=headers)
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read(max_bytes).decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        return LogSnapshot(kind=kind, available=False, snippet=f"{exc.__class__.__name__}: {exc}")

    lines = [line for line in raw.splitlines() if line.strip()]
    if not lines:
        return LogSnapshot(kind=kind, available=False, snippet="No log data returned.")

    snippet = "\n".join(lines[:80])
    return LogSnapshot(kind=kind, available=True, snippet=snippet)


def format_check_result(result: CheckResult) -> str:
    marker = "PASS" if result.ok else "FAIL"
    return f"[{marker}] {result.name}: {result.detail}"


def build_report(
    *,
    repo_sha: str,
    expected_sha: str | None,
    space_id: str,
    base_url: str,
    runtime: RuntimeSnapshot,
    probe_results: list[CheckResult],
    run_log: LogSnapshot,
    build_log: LogSnapshot,
) -> str:
    failures = [result for result in probe_results if not result.ok]
    lines = [
        "# Submission Evidence Pack",
        "",
        f"Generated: {dt.datetime.now(dt.timezone.utc).isoformat()}",
        f"Repo SHA: {repo_sha}",
        f"Expected SHA: {expected_sha or 'not-set'}",
        f"Space: {space_id}",
        f"Base URL: {base_url}",
        f"Runtime stage: {runtime.stage}",
        f"Runtime SHA: {runtime.sha}",
        f"Runtime hardware: {json.dumps(runtime.hardware, sort_keys=True)}",
        f"Runtime domains: {json.dumps(runtime.domains, sort_keys=True)}",
        "",
        "## Live Probe Summary",
        f"Total checks: {len(probe_results)}",
        f"Passed: {len(probe_results) - len(failures)}",
        f"Failed: {len(failures)}",
        "",
    ]

    lines.append("### Probe Details")
    for result in probe_results:
        lines.append(format_check_result(result))

    lines.extend(
        [
            "",
            "## Log Samples",
            f"Run logs available: {run_log.available}",
            "```",
            run_log.snippet,
            "```",
            f"Build logs available: {build_log.available}",
            "```",
            build_log.snippet,
            "```",
            "",
            "## Go/No-Go",
            "GO" if not failures and runtime.stage == "RUNNING" and (expected_sha is None or runtime.sha.startswith(expected_sha)) else "NO-GO",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def build_json_report(
    *,
    repo_sha: str,
    expected_sha: str | None,
    space_id: str,
    base_url: str,
    runtime: RuntimeSnapshot,
    probe_results: list[CheckResult],
    run_log: LogSnapshot,
    build_log: LogSnapshot,
) -> dict[str, Any]:
    failures = [result for result in probe_results if not result.ok]
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repo_sha": repo_sha,
        "expected_sha": expected_sha,
        "space_id": space_id,
        "base_url": base_url,
        "runtime": asdict(runtime),
        "probe_results": [asdict(result) for result in probe_results],
        "run_log": asdict(run_log),
        "build_log": asdict(build_log),
        "go": not failures and runtime.stage == "RUNNING" and (expected_sha is None or runtime.sha.startswith(expected_sha)),
    }


def capture_evidence(space_id: str, base_url: str, expected_sha: str | None, token: str | None) -> tuple[str, dict[str, Any]]:
    repo_sha = get_git_sha()
    runtime = fetch_runtime_snapshot(space_id)
    probe_results = run_probe(base_url.rstrip("/"))
    run_log = fetch_log_snippet(space_id, "run", token)
    build_log = fetch_log_snippet(space_id, "build", token)

    markdown = build_report(
        repo_sha=repo_sha,
        expected_sha=expected_sha,
        space_id=space_id,
        base_url=base_url,
        runtime=runtime,
        probe_results=probe_results,
        run_log=run_log,
        build_log=build_log,
    )
    payload = build_json_report(
        repo_sha=repo_sha,
        expected_sha=expected_sha,
        space_id=space_id,
        base_url=base_url,
        runtime=runtime,
        probe_results=probe_results,
        run_log=run_log,
        build_log=build_log,
    )
    return markdown, payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture a frozen submission evidence pack for the live Space")
    parser.add_argument("--space-id", default=os.getenv("HF_SPACE_ID"), help="Hugging Face Space id, for example sagar-grv/anything_you_want")
    parser.add_argument("--base-url", default=os.getenv("SPACE_BASE_URL", "https://sagar-grv-anything-you-want.hf.space"), help="Live Space base URL")
    parser.add_argument("--expected-sha", default=os.getenv("EXPECTED_SPACE_SHA"), help="Expected deployed commit SHA for this submission cycle")
    parser.add_argument("--output", default="submission-evidence.md", help="Markdown output path")
    parser.add_argument("--json-output", default=None, help="Optional JSON output path (defaults to sibling .json)")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when runtime/probe checks do not satisfy the go gate")
    args = parser.parse_args(argv)

    if not args.space_id:
        raise SystemExit("--space-id or HF_SPACE_ID is required")

    token = os.getenv("HF_TOKEN")
    markdown, payload = capture_evidence(args.space_id, args.base_url, args.expected_sha, token)

    output_path = Path(args.output)
    output_path.write_text(markdown, encoding="utf-8")

    json_output_path = Path(args.json_output) if args.json_output else output_path.with_suffix(".json")
    json_output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    print(markdown, end="")

    if args.strict and not payload["go"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())