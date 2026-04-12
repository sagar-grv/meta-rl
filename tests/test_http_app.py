from fastapi.testclient import TestClient

from support_queue_env.server.app import app


def test_ui_route_returns_tester_page():
    with TestClient(app) as client:
        response = client.get("/ui/")

    assert response.status_code == 200
    assert "Support Queue Agent Tester" in response.text


def test_ui_api_preserves_selected_task_for_step():
    with TestClient(app) as client:
        reset_response = client.post(
            "/ui-api/reset",
            json={"task_name": "escalation_resolution", "seed": 7},
        )
        step_response = client.post(
            "/ui-api/step",
            json={
                "task_name": "escalation_resolution",
                "seed": 7,
                "action": {
                    "route": "escalate",
                    "reply": "I will escalate this case with a compliant handoff.",
                },
            },
        )

    assert reset_response.status_code == 200
    assert step_response.status_code == 200
    assert reset_response.json()["task_name"] == "escalation_resolution"
    assert step_response.json()["task_name"] == "escalation_resolution"
    assert step_response.json()["observation"]["ticket_id"] == "ticket-003"


def test_health_endpoint_returns_ok():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_reset_step_and_state_endpoints_work():
    with TestClient(app) as client:
        reset_response = client.post(
            "/reset",
            json={"task_name": "ticket_triage", "seed": 7},
        )
        step_response = client.post(
            "/step",
            json={"action": {"route": "support", "reply": "Please reset your password."}},
        )
        state_response = client.get("/state")

    assert reset_response.status_code == 200
    reset_body = reset_response.json()
    assert reset_body["observation"]["observation"]["ticket_id"] == "ticket-001"
    assert 0.0 < float(reset_response.json()["reward"]) < 1.0
    assert step_response.status_code == 200
    assert 0.0 < float(step_response.json()["reward"]) < 1.0
    assert state_response.status_code == 200
    assert isinstance(state_response.json().get("step_count"), int)


def test_reset_unknown_task_falls_back_to_default_task_with_valid_score():
    with TestClient(app) as client:
        reset_response = client.post(
            "/reset",
            json={"task_name": "unknown_hidden_task", "seed": 7},
        )

    assert reset_response.status_code == 200
    body = reset_response.json()
    assert body["observation"]["info"]["task_name"] == "ticket_triage"
    assert 0.0 < float(body["reward"]) < 1.0
