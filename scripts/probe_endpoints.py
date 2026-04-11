from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


TASKS = ["ticket_triage", "reply_drafting", "escalation_resolution"]


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def _request_json(base_url: str, path: str, method: str = "GET", payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(f"{base_url}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            if body:
                try:
                    parsed = json.loads(body)
                except json.JSONDecodeError:
                    parsed = {"raw": body}
            else:
                parsed = {}
            return int(resp.status), parsed
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        if body:
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = {"raw": body}
        else:
            parsed = {}
        return int(exc.code), parsed


def _check(name: str, condition: bool, detail_ok: str, detail_fail: str) -> CheckResult:
    return CheckResult(name=name, ok=condition, detail=detail_ok if condition else detail_fail)


def _extract_reward(body: dict[str, Any] | Any) -> float:
    if not isinstance(body, dict):
        return -1.0
    reward = body.get("reward", -1)
    if isinstance(reward, dict):
        reward = reward.get("score", -1)
    try:
        return float(reward)
    except (TypeError, ValueError):
        return -1.0


def run_probe(base_url: str) -> list[CheckResult]:
    results: list[CheckResult] = []

    status, root_body = _request_json(base_url, "/", "GET")
    root_ok = (status == 200 and root_body.get("status") in {"ok", "healthy"}) or status == 404
    results.append(_check("root_compat", root_ok, "root endpoint compatibility check passed", f"root failed: status={status}, body={root_body}"))

    status, health_body = _request_json(base_url, "/health", "GET")
    results.append(
        _check(
            "health_200",
            status == 200 and health_body.get("status") in {"ok", "healthy"},
            "health returned 200 with valid status",
            f"health failed: status={status}, body={health_body}",
        )
    )

    status, reset_body = _request_json(base_url, "/reset", "POST")
    reset_reward = _extract_reward(reset_body)
    reset_obs = reset_body.get("observation", {}).get("observation", {}) if isinstance(reset_body, dict) else {}
    results.append(
        _check(
            "reset_without_body",
            status == 200 and isinstance(reset_obs, dict) and reset_obs.get("ticket_id") and 0.0 < reset_reward < 1.0,
            "reset accepted POST without body and score in (0,1)",
            f"reset no-body failed: status={status}, body={reset_body}",
        )
    )

    for task in TASKS:
        status, reset_task_body = _request_json(base_url, "/reset", "POST", {"task_name": task, "seed": 7})
        observation = reset_task_body.get("observation", {}).get("observation", {}) if isinstance(reset_task_body, dict) else {}
        reset_reward = _extract_reward(reset_task_body)
        task_ok = (
            status == 200
            and observation.get("ticket_id")
            and observation.get("subject")
            and observation.get("summary")
            and 0.0 < reset_reward < 1.0
        )
        results.append(
            _check(
                f"task_reset_{task}",
                bool(task_ok),
                f"task {task} reset returned observation and score in (0,1)",
                f"task {task} reset failed: status={status}, body={reset_task_body}",
            )
        )

        action = {"route": "support", "reply": "I can help resolve login refund escalate request."}
        status, step_body = _request_json(base_url, "/step", "POST", {"action": action})
        reward = _extract_reward(step_body)
        done = bool(step_body.get("done")) if isinstance(step_body, dict) else False
        strict_range = 0.0 < reward < 1.0
        results.append(
            _check(
                f"task_step_score_range_{task}",
                status == 200 and strict_range and done,
                f"task {task} step score in (0,1) and done=true",
                f"task {task} invalid step: status={status}, reward={reward}, done={done}, body={step_body}",
            )
        )

        status, state_body = _request_json(base_url, "/state", "GET")
        state_ok = status == 200 and isinstance(state_body.get("step_count"), int)
        results.append(
            _check(
                f"state_progress_{task}",
                state_ok,
                f"state endpoint returned valid step_count for {task}",
                f"state mismatch for {task}: status={status}, body={state_body}",
            )
        )

        status, _ = _request_json(base_url, "/reset", "POST", {"task_name": task, "seed": 7})
        status1, step1 = _request_json(base_url, "/step", "POST", {"action": action})
        status, _ = _request_json(base_url, "/reset", "POST", {"task_name": task, "seed": 7})
        status2, step2 = _request_json(base_url, "/step", "POST", {"action": action})
        deterministic = (
            status1 == 200
            and status2 == 200
            and step1.get("reward") == step2.get("reward")
            and step1.get("observation", {}).get("observation", {}).get("status")
            == step2.get("observation", {}).get("observation", {}).get("status")
        )
        results.append(
            _check(
                f"determinism_{task}",
                deterministic,
                f"deterministic step behavior confirmed for {task}",
                f"nondeterministic output for {task}: step1={step1}, step2={step2}",
            )
        )

    unknown_status, unknown_body = _request_json(base_url, "/reset", "POST", {"task_name": "unknown_hidden_task", "seed": 7})
    unknown_reward = _extract_reward(unknown_body)
    unknown_task = unknown_body.get("observation", {}).get("info", {}).get("task_name") if isinstance(unknown_body, dict) else None
    results.append(
        _check(
            "unknown_task_fallback",
            unknown_status == 200 and unknown_task in TASKS and 0.0 < unknown_reward < 1.0,
            "unknown task reset safely fell back to a supported task with score in (0,1)",
            f"unknown task handling invalid: status={unknown_status}, body={unknown_body}",
        )
    )

    status, _ = _request_json(base_url, "/step", "POST", {"action": {"route": 123, "reply": 456}})
    results.append(
        _check(
            "invalid_action_rejected",
            status >= 400,
            "invalid action payload rejected",
            f"invalid action unexpectedly accepted: status={status}",
        )
    )

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluator-like local endpoint probe for OpenEnv submission checks")
    parser.add_argument("--base-url", default="http://127.0.0.1:7860", help="Base URL of the running environment server")
    args = parser.parse_args()

    results = run_probe(args.base_url.rstrip("/"))
    failed = [r for r in results if not r.ok]

    print("\nEndpoint Probe Report")
    print("====================")
    for r in results:
        marker = "PASS" if r.ok else "FAIL"
        print(f"[{marker}] {r.name}: {r.detail}")

    print("\nSummary")
    print("=======")
    print(f"total={len(results)} passed={len(results)-len(failed)} failed={len(failed)}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
