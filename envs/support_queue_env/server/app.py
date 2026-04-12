from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import Body
from fastapi.staticfiles import StaticFiles

try:
    from openenv.core.env_server.http_server import create_app
except Exception:  # pragma: no cover
    from openenv_core.env_server.http_server import create_app

from support_queue_env.models import SupportQueueAction, SupportQueueObservation
from support_queue_env.server.your_environment import SupportQueueEnvironment

app = create_app(
    SupportQueueEnvironment,
    SupportQueueAction,
    SupportQueueObservation,
    env_name="support_queue_env",
)

WEB_DIR = Path(__file__).resolve().parents[3] / "web"
if WEB_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(WEB_DIR), html=True), name="ui")


_ui_env: SupportQueueEnvironment | None = None


def _ensure_ui_env(task_name: str | None, seed: int | None) -> SupportQueueEnvironment:
    global _ui_env
    if _ui_env is None:
        _ui_env = SupportQueueEnvironment(seed=seed, task_name=task_name or "ticket_triage")
        return _ui_env

    if task_name and _ui_env.task_name != task_name:
        _ui_env = SupportQueueEnvironment(seed=seed, task_name=task_name)
        return _ui_env

    if seed is not None:
        _ui_env.seed = seed
    return _ui_env


@app.post("/ui-api/reset")
def ui_reset(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    task_name = payload.get("task_name")
    seed = payload.get("seed")
    env = _ensure_ui_env(task_name, seed)
    result = env.reset(task_name=task_name, seed=seed)
    return {
        "task_name": env.task_name,
        "reward": result.reward,
        "done": result.done,
        "observation": result.observation.model_dump(),
        "info": result.info,
    }


@app.post("/ui-api/step")
def ui_step(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    task_name = payload.get("task_name")
    seed = payload.get("seed")
    env = _ensure_ui_env(task_name, seed)

    action_payload = payload.get("action") or {}
    action = SupportQueueAction(**action_payload)
    result = env.step(action)
    return {
        "task_name": env.task_name,
        "reward": result.reward,
        "done": result.done,
        "observation": result.observation.model_dump(),
        "info": result.info,
    }


@app.get("/ui-api/state")
def ui_state() -> dict[str, Any]:
    env = _ensure_ui_env(task_name=None, seed=None)
    return env.state.model_dump()


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("API_PORT", "7860")))


if __name__ == "__main__":
    main()
