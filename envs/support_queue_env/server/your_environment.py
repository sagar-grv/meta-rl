from __future__ import annotations

import re

from support_queue_env.models import (
    SupportQueueAction,
    SupportQueueObservation,
    SupportQueueReward,
    SupportQueueState,
    StepResult,
)
from support_queue_env.tasks import get_task_spec


class SupportQueueEnvironment:
    def __init__(self, seed: int | None = None, task_name: str = "ticket_triage") -> None:
        self.seed = seed
        self.task_name = task_name
        self._task_spec = get_task_spec(task_name)
        self._state = SupportQueueState(
            step_count=0,
            episode_done=False,
            current_ticket_id=self._task_spec.ticket_id,
            task_name=self._task_spec.name,
        )

    def reset(self) -> StepResult:
        self._task_spec = get_task_spec(self.task_name)
        self._state = SupportQueueState(
            step_count=0,
            episode_done=False,
            current_ticket_id=self._task_spec.ticket_id,
            task_name=self._task_spec.name,
        )
        return StepResult(
            observation=SupportQueueObservation(
                ticket_id=self._task_spec.ticket_id,
                status="open",
                subject=self._task_spec.subject,
                summary=self._task_spec.summary,
            ),
            reward=SupportQueueReward(score=0.0),
            done=False,
            info={"task_name": self._state.task_name},
        )

    def step(self, action: SupportQueueAction) -> StepResult:
        self._state = self._state.model_copy(update={"step_count": self._state.step_count + 1})
        route = action.route.strip().lower()
        expected_route = self._task_spec.expected_route
        route_is_correct = route in {expected_route, "support"} if expected_route == "support" else route == expected_route
        reply_lower = action.reply.lower()
        reply_has_keyword = self._task_spec.success_keyword in reply_lower

        reply_words = set(re.findall(r"[a-zA-Z]{3,}", reply_lower))
        context_words = set(re.findall(r"[a-zA-Z]{3,}", f"{self._task_spec.subject} {self._task_spec.summary}".lower()))
        overlap = len(reply_words & context_words)
        relevance_ratio = overlap / max(min(len(context_words), 6), 1)

        stuffing_terms = {"login", "refund", "escalate", "policy", "billing", "handoff", "dispute", "password", "account"}
        stuffing_count = sum(1 for token in stuffing_terms if token in reply_lower)

        generic_reply = len(reply_words) < 3 or reply_lower.strip() in {"", "i can help.", "please help", "i can help"}
        overlong_reply = len(action.reply) > 400 or len(reply_words) > 120

        keyword_credit = 0.22 if (reply_has_keyword and route_is_correct) else (0.05 if reply_has_keyword else 0.0)
        quality_credit = 0.12 if relevance_ratio >= 0.20 else 0.0
        generic_penalty = 0.12 if generic_reply else 0.0
        overlong_penalty = 0.18 if overlong_reply else 0.0
        stuffing_penalty = 0.28 if stuffing_count >= 4 else 0.0

        # Keep task score strictly inside (0, 1) and discourage shortcut strategies.
        reward_value = 0.08 + (0.55 if route_is_correct else 0.0) + keyword_credit + quality_credit
        reward_value -= generic_penalty + overlong_penalty + stuffing_penalty
        reward_value = min(max(reward_value, 0.01), 0.99)
        self._state = self._state.model_copy(update={"episode_done": True})
        return StepResult(
            observation=SupportQueueObservation(
                ticket_id=self._state.current_ticket_id,
                status="resolved" if route_is_correct else "needs_review",
                subject=self._task_spec.subject,
                summary=self._task_spec.summary,
            ),
            reward=SupportQueueReward(score=reward_value),
            done=True,
            info={
                "route": action.route,
                "reply": action.reply,
                "task_name": self._state.task_name,
                "route_is_correct": route_is_correct,
            },
        )

    def state(self) -> SupportQueueState:
        return self._state
