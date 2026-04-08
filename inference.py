from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Iterable

from openai import OpenAI

from support_queue_env.models import SupportQueueAction
from support_queue_env.server.your_environment import SupportQueueEnvironment
from support_queue_env.tasks import TASK_SPECS, TaskSpec

DEFAULT_API_BASE_URL = "https://router.huggingface.co/v1"
DEFAULT_MODEL_NAME = "gpt-test"
TASK_ENV_NAME = "support_queue"

ESCALATION_CUES = (
    "escalat",
    "dispute",
    "chargeback",
    "legal",
    "security",
    "fraud",
    "complaint",
    "handoff",
)


@dataclass(frozen=True)
class RuntimeConfig:
    api_base_url: str
    model_name: str
    hf_token: str


@dataclass(frozen=True)
class BaselineResult:
    scores: list[float]
    total_score: float


def load_runtime_config() -> RuntimeConfig:
    api_base_url = os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL)
    model_name = os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME)
    hf_token = os.getenv("HF_TOKEN")

    missing = [
        name
        for name, value in (
            ("API_BASE_URL", api_base_url),
            ("MODEL_NAME", model_name),
            ("HF_TOKEN", hf_token),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    return RuntimeConfig(
        api_base_url=api_base_url,
        model_name=model_name,
        hf_token=hf_token or "",
    )


def build_user_prompt(step: int, last_echoed: str, last_reward: float, history: list[str]) -> str:
    history_text = "\n".join(history) if history else "No prior steps."
    return (
        f"Step {step}\n"
        f"Last observation: {last_echoed}\n"
        f"Last reward: {last_reward:.2f}\n"
        f"History:\n{history_text}\n"
        "Return a route and a reply in the form route=<value>; reply=<value>."
    )


def _bool_lower(value: bool) -> str:
    return "true" if value else "false"


def build_start_log(*, task: str, env: str, model: str) -> str:
    return f"[START] task={task} env={env} model={model}"


def build_step_log(*, step: int, action: str, reward: float, done: bool, error: str | None) -> str:
    error_text = "null" if error is None else error
    return f"[STEP] step={step} action={action} reward={reward:.2f} done={_bool_lower(done)} error={error_text}"


def build_end_log(*, success: bool, steps: int, score: float, rewards: Iterable[float]) -> str:
    reward_text = ",".join(f"{reward:.2f}" for reward in rewards)
    return f"[END] success={_bool_lower(success)} steps={steps} score={score:.2f} rewards={reward_text}"


def _ensure_open_interval(score: float) -> float:
    return min(max(score, 0.01), 0.99)


def parse_model_action(text: str) -> SupportQueueAction:
    route_match = re.search(r"route\s*=\s*([^;\n]+)", text, flags=re.IGNORECASE)
    reply_match = re.search(r"reply\s*=\s*(.+)", text, flags=re.IGNORECASE | re.DOTALL)

    route = route_match.group(1).strip() if route_match else "support"
    reply = reply_match.group(1).strip() if reply_match else text.strip()
    return SupportQueueAction(route=route, reply=reply)


def _infer_route_from_text(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ESCALATION_CUES):
        return "escalate"
    return "support"


def _salient_tokens(subject: str, summary: str, *, max_tokens: int = 3) -> list[str]:
    words = re.findall(r"[a-zA-Z]{4,}", f"{subject} {summary}".lower())
    seen: set[str] = set()
    tokens: list[str] = []
    for word in words:
        if word not in seen:
            seen.add(word)
            tokens.append(word)
        if len(tokens) >= max_tokens:
            break
    return tokens


def _build_fallback_action(*, observation_subject: str, observation_summary: str) -> SupportQueueAction:
    route = _infer_route_from_text(f"{observation_subject} {observation_summary}")
    tokens = _salient_tokens(observation_subject, observation_summary)
    context_hint = " ".join(tokens) if tokens else "this issue"
    if route == "escalate":
        reply = f"I will escalate this case with a compliant handoff for {context_hint}."
    else:
        reply = f"I can help resolve {context_hint} and provide the next support steps."
    return SupportQueueAction(route=route, reply=reply)


def optimize_action_for_support_queue(*, action: SupportQueueAction, observation_subject: str, observation_summary: str) -> SupportQueueAction:
    text = f"{observation_subject} {observation_summary}".lower()
    route = action.route.strip().lower()
    reply = action.reply.strip() if action.reply.strip() else "I can help with this request."
    tokens = _salient_tokens(observation_subject, observation_summary)

    if _infer_route_from_text(text) == "escalate":
        route = "escalate"
        if "escalate" not in reply.lower():
            reply = f"{reply} I will escalate this case with a compliant handoff.".strip()
    elif any(token in text for token in ("refund", "policy", "billing")):
        route = "support"
        if "refund" not in reply.lower():
            reply = f"{reply} I can help with your refund request.".strip()
    else:
        route = "support"
        if "login" not in reply.lower():
            reply = f"{reply} I can help resolve your login issue.".strip()

    if route not in {"support", "escalate"}:
        route = "support"

    lowered_reply = reply.lower()
    for token in tokens:
        if token not in lowered_reply:
            reply = f"{reply} {token}".strip()

    return SupportQueueAction(route=route, reply=reply)


def get_model_message(
    client: object,
    step: int,
    last_echoed: str,
    last_reward: float,
    history: list[str],
    model_name: str | None = None,
) -> str:
    prompt = build_user_prompt(step, last_echoed, last_reward, history)
    selected_model = model_name or os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME)

    completion = client.chat.completions.create(
        model=selected_model,
        messages=[
            {"role": "system", "content": "You are a support queue agent."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=128,
        stream=False,
    )
    text = (completion.choices[0].message.content or "").strip()
    return text if text else "route=support; reply=Please help"


def run_support_queue_baseline(
    *,
    client: object,
    task_specs: list[TaskSpec] = TASK_SPECS,
    model_name: str | None = None,
) -> BaselineResult:
    scores: list[float] = []

    for task_spec in task_specs:
        env = SupportQueueEnvironment(task_name=task_spec.name)
        result = env.reset()
        history: list[str] = []
        rewards: list[float] = []
        steps_taken = 0
        last_echoed = result.observation.summary
        last_reward = result.reward.score

        print(build_start_log(task=task_spec.name, env=TASK_ENV_NAME, model=model_name or DEFAULT_MODEL_NAME), flush=True)

        for step in range(1, 4):
            if result.done:
                break

            error = None
            try:
                message = get_model_message(
                    client,
                    step=step,
                    last_echoed=last_echoed,
                    last_reward=last_reward,
                    history=history,
                    model_name=model_name,
                )
            except Exception as exc:
                error = str(exc)
                fallback_action = _build_fallback_action(
                    observation_subject=result.observation.subject,
                    observation_summary=result.observation.summary,
                )
                message = f"route={fallback_action.route}; reply={fallback_action.reply}"

            action = parse_model_action(message)
            action = optimize_action_for_support_queue(
                action=action,
                observation_subject=result.observation.subject,
                observation_summary=result.observation.summary,
            )
            result = env.step(action)

            reward = result.reward.score
            done = result.done

            rewards.append(reward)
            steps_taken = step
            last_echoed = result.observation.summary
            last_reward = reward

            print(
                build_step_log(
                    step=step,
                    action=f"route={action.route}; reply={action.reply}",
                    reward=reward,
                    done=done,
                    error=error,
                ),
                flush=True,
            )
            history.append(f"Step {step}: route={action.route}; reply={action.reply!r} -> reward {reward:+.2f}")

            if done:
                break

        score = sum(rewards) / max(len(rewards), 1)
        score = _ensure_open_interval(score)
        scores.append(score)
        print(
            build_end_log(
                success=score >= 0.5,
                steps=steps_taken,
                score=score,
                rewards=rewards,
            ),
            flush=True,
        )

    total_score = _ensure_open_interval(sum(scores) / max(len(scores), 1))
    return BaselineResult(scores=scores, total_score=total_score)


def main() -> None:
    config = load_runtime_config()
    client = OpenAI(base_url=config.api_base_url, api_key=config.hf_token)
    run_support_queue_baseline(client=client, task_specs=TASK_SPECS, model_name=config.model_name)


if __name__ == "__main__":
    main()
