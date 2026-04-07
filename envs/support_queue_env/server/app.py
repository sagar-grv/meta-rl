from __future__ import annotations

from fastapi import Body, FastAPI
from pydantic import BaseModel

from support_queue_env.models import SupportQueueAction
from support_queue_env.server.your_environment import SupportQueueEnvironment

app = FastAPI(title="Support Queue OpenEnv")
environment = SupportQueueEnvironment()


class ResetRequest(BaseModel):
    task_name: str = "ticket_triage"
    seed: int | None = None


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/reset")
def reset(request: ResetRequest | None = Body(default=None)) -> dict[str, object]:
    global environment
    task_name = request.task_name if request is not None else "ticket_triage"
    seed = request.seed if request is not None else None
    environment = SupportQueueEnvironment(seed=seed, task_name=task_name)
    result = environment.reset()
    return result.model_dump()


@app.post("/step")
def step(action: SupportQueueAction) -> dict[str, object]:
    result = environment.step(action)
    return result.model_dump()


@app.get("/state")
def state() -> dict[str, object]:
    return environment.state().model_dump()
