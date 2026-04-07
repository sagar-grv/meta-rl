from __future__ import annotations

from support_queue_env.models import SupportQueueAction
from support_queue_env.server.your_environment import SupportQueueEnvironment


class SupportQueueClient:
    def __init__(self, *, seed: int | None = None, task_name: str = "ticket_triage") -> None:
        self._environment = SupportQueueEnvironment(seed=seed, task_name=task_name)

    def reset(self):
        return self._environment.reset()

    def step(self, action: SupportQueueAction):
        return self._environment.step(action)

    def state(self):
        return self._environment.state()
