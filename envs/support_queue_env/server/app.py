from __future__ import annotations

import os
from pathlib import Path

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


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("API_PORT", "7860")))


if __name__ == "__main__":
    main()
