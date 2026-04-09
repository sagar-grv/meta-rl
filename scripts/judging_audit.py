from __future__ import annotations

import json
from dataclasses import dataclass

from support_queue_env.models import SupportQueueAction
from support_queue_env.server.your_environment import SupportQueueEnvironment
from support_queue_env.tasks import TASK_SPECS


@dataclass(frozen=True)
class AuditCheck:
    name: str
    passed: bool
    detail: str


def _score_once(task_name: str, route: str, reply: str) -> float:
    env = SupportQueueEnvironment(seed=7, task_name=task_name)
    env.reset()
    return env.step(SupportQueueAction(route=route, reply=reply)).reward.score


def _policy_scores() -> dict[str, list[float]]:
    def contextual(subject: str, summary: str) -> tuple[str, str]:
        text = f"{subject} {summary}".lower()
        if "escalat" in text or "dispute" in text:
            return "escalate", "I will escalate this case with a compliant handoff."
        if "refund" in text or "billing" in text or "policy" in text:
            return "support", "I can help with your refund request."
        return "support", "I can help resolve your login issue."

    policies = {
        "contextual": contextual,
        "always_support": lambda s, sm: ("support", "I can help."),
        "polite_generic": lambda s, sm: ("support", "Thank you for contacting support. We are reviewing your case."),
        "one_template": lambda s, sm: ("support", "I understand your concern and will assist with policy-compliant next steps."),
        "keyword_stuff": lambda s, sm: (
            "support",
            "login refund escalate policy billing handoff dispute account password customer request issue",
        ),
        "repetitive_keyword": lambda s, sm: ("support", "refund refund refund refund refund refund"),
        "keyword_only": lambda s, sm: ("support", "login"),
        "empty_reply": lambda s, sm: ("support", ""),
        "overlong_irrelevant": lambda s, sm: ("support", " ".join(["lorem"] * 300)),
    }

    results: dict[str, list[float]] = {k: [] for k in policies}
    for task_spec in TASK_SPECS:
        env = SupportQueueEnvironment(seed=7, task_name=task_spec.name)
        obs = env.reset().observation
        for name, policy in policies.items():
            route, reply = policy(obs.subject, obs.summary)
            score = _score_once(task_spec.name, route, reply)
            results[name].append(score)
    return results


def run_judging_audit() -> list[AuditCheck]:
    checks: list[AuditCheck] = []

    # Layer 1: interface/protocol shape and strict score range.
    env = SupportQueueEnvironment(seed=7, task_name="ticket_triage")
    reset_result = env.reset()
    step_result = env.step(SupportQueueAction(route="support", reply="I can help resolve your login issue."))
    checks.append(
        AuditCheck(
            name="interface_contract",
            passed=(
                bool(reset_result.observation.ticket_id)
                and isinstance(step_result.done, bool)
                and isinstance(step_result.info, dict)
                and 0.0 < step_result.reward.score < 1.0
            ),
            detail="reset/step types valid and score strictly inside (0,1)",
        )
    )

    # Layer 2/3/6: task integrity, reward quality, anti-exploit ordering.
    scores = _policy_scores()
    avg = {name: sum(vals) / len(vals) for name, vals in scores.items()}
    checks.append(
        AuditCheck(
            name="policy_ordering",
            passed=(
                avg["contextual"] > avg["keyword_stuff"] > avg["always_support"]
                and avg["contextual"] > avg["repetitive_keyword"]
                and avg["contextual"] > avg["polite_generic"]
                and avg["contextual"] > avg["one_template"]
                and avg["keyword_only"] <= 0.45
                and avg["overlong_irrelevant"] <= 0.25
                and avg["overlong_irrelevant"] < avg["contextual"]
            ),
            detail=(
                f"avg(contextual)={avg['contextual']:.3f}, avg(keyword_stuff)={avg['keyword_stuff']:.3f}, "
                f"avg(polite_generic)={avg['polite_generic']:.3f}, avg(one_template)={avg['one_template']:.3f}, "
                f"avg(repetitive_keyword)={avg['repetitive_keyword']:.3f}, avg(keyword_only)={avg['keyword_only']:.3f}, "
                f"avg(always_support)={avg['always_support']:.3f}, "
                f"avg(overlong_irrelevant)={avg['overlong_irrelevant']:.3f}"
            ),
        )
    )

    checks.append(
        AuditCheck(
            name="hard_task_challenge",
            passed=(scores["contextual"][2] > scores["always_support"][2] and scores["contextual"][2] > scores["keyword_stuff"][2]),
            detail=(
                f"hard-task scores: contextual={scores['contextual'][2]:.3f}, "
                f"always_support={scores['always_support'][2]:.3f}, keyword_stuff={scores['keyword_stuff'][2]:.3f}"
            ),
        )
    )

    # Layer 4/5: determinism and reproducibility.
    r1 = _score_once("reply_drafting", "support", "I can help with your refund request.")
    r2 = _score_once("reply_drafting", "support", "I can help with your refund request.")
    checks.append(
        AuditCheck(
            name="determinism",
            passed=(r1 == r2),
            detail=f"repeat scores={r1:.3f},{r2:.3f}",
        )
    )

    return checks


def main() -> int:
    checks = run_judging_audit()
    failed = [c for c in checks if not c.passed]

    print("Judging Audit Report")
    print("====================")
    for check in checks:
        marker = "PASS" if check.passed else "FAIL"
        print(f"[{marker}] {check.name}: {check.detail}")

    summary = {
        "total": len(checks),
        "passed": len(checks) - len(failed),
        "failed": len(failed),
    }
    print("\nSummary")
    print("=======")
    print(json.dumps(summary, indent=2))

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
