from fastapi.testclient import TestClient

from support_queue_env.server.app import app


def test_health_endpoint_returns_ok():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_reset_step_and_state_endpoints_work():
    with TestClient(app) as client:
        reset_response = client.post(
            "/reset",
            json={"task_name": "ticket_triage", "seed": 7},
        )
        step_response = client.post(
            "/step",
            json={"route": "support", "reply": "Please reset your password."},
        )
        state_response = client.get("/state")

    assert reset_response.status_code == 200
    assert reset_response.json()["observation"]["ticket_id"] == "ticket-001"
    assert step_response.status_code == 200
    assert step_response.json()["reward"]["score"] >= 0.0
    assert state_response.status_code == 200
    assert state_response.json()["step_count"] == 1
