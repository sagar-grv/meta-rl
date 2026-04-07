from __future__ import annotations

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
        reply_has_keyword = self._task_spec.success_keyword in action.reply.lower()
        reward_value = 0.2 + (0.5 if route_is_correct else 0.0) + (0.3 if reply_has_keyword else 0.0)
        reward_value = min(reward_value, 1.0)
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
