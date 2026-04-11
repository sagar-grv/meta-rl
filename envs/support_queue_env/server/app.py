from __future__ import annotations

import os

try:
    from openenv.core.env_server.http_server import create_app
except Exception:  # pragma: no cover
    from openenv_core.env_server.http_server import create_app

from support_queue_env.models import SupportQueueAction, SupportQueueObservation
from support_queue_env.server.your_environment import SupportQueueEnvironment


_environment = SupportQueueEnvironment()


def create_environment() -> SupportQueueEnvironment:
    return _environment


app = create_app(
    create_environment,
    SupportQueueAction,
    SupportQueueObservation,
    env_name="support_queue_env",
    max_concurrent_envs=1,
)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("API_PORT", "7860")))


if __name__ == "__main__":
    main()
