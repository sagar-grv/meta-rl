import importlib
import os

from fastapi.testclient import TestClient


def _reload_app_with_dashboard_flag(flag_value: str | None):
    env_name = "ENABLE_LOCAL_TEST_DASHBOARD"
    original = os.environ.get(env_name)

    if flag_value is None:
        os.environ.pop(env_name, None)
    else:
        os.environ[env_name] = flag_value

    import support_queue_env.server.app as app_module

    app_module = importlib.reload(app_module)

    if original is None:
        os.environ.pop(env_name, None)
    else:
        os.environ[env_name] = original

    return app_module.app


def test_ui_routes_are_hidden_when_dashboard_flag_is_not_enabled():
    app = _reload_app_with_dashboard_flag(None)

    with TestClient(app) as client:
        ui_response = client.get("/ui/")
        ui_api_response = client.post("/ui-api/reset", json={"task_name": "ticket_triage", "seed": 7})

    assert ui_response.status_code == 404
    assert ui_api_response.status_code == 404
