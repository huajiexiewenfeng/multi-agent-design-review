from fastapi.testclient import TestClient
import time

import backend.app.api as api_module
from backend.app.main import app
from backend.app.services import runner_service


def test_create_run_api(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)

    response = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"})

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "clarification"
    assert body["status"] == "waiting_input"


def test_update_agent_config_api(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.put(
        f"/api/runs/{created['run_id']}/agents/architect/config",
        json={"runner": "claude-code", "model": "opus"},
    )

    assert response.status_code == 200
    architect = next(agent for agent in response.json()["agents"] if agent["id"] == "architect")
    assert architect["runner"] == "claude-code"
    assert architect["model"] == "opus"
    assert architect["llm_name"] == "opus"


def test_graph_step_api_uses_configured_runner_and_generates_prompt(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    monkeypatch.setattr(runner_service, "resolve_runner_command", lambda runner, model=None: None)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()
    client.put(
        f"/api/runs/{created['run_id']}/agents/architect/config",
        json={"runner": "claude-code", "llm_name": "claude-sonnet-4.5"},
    )

    response = client.post(f"/api/runs/{created['run_id']}/graph/step", json={"confirmed": True})

    assert response.status_code == 200
    body = response.json()
    assert body["graph_state"]["run_id"] == created["run_id"]
    assert body["projection"]["stage"] == "clarification"
    run_dir = tmp_path / created["run_id"]
    assert (run_dir / "agents" / "architect" / "clarification_prompt.md").is_file()
    assert "waiting for manual submission" in (run_dir / "runner_logs" / "architect" / "manual.log").read_text(
        encoding="utf-8"
    )


def test_graph_step_merges_clarification_questions_when_outputs_are_ready(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(f"/api/runs/{created['run_id']}/graph/step", json={"confirmed": True})

    assert response.status_code == 200
    run_dir = tmp_path / created["run_id"]
    assert (run_dir / "input" / "clarification_questions.json").is_file()
    assert (run_dir / "input" / "clarification_questions.md").is_file()


def test_graph_step_job_runs_in_background(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(f"/api/runs/{created['run_id']}/graph/step/jobs", json={"confirmed": True})

    assert response.status_code == 200
    job = response.json()
    assert job["run_id"] == created["run_id"]
    assert job["status"] in {"queued", "running", "succeeded"}

    for _ in range(20):
        job = client.get(f"/api/runs/{created['run_id']}/jobs/{job['id']}").json()
        if job["status"] == "succeeded":
            break
        time.sleep(0.05)

    assert job["status"] == "succeeded"
    assert job["projection"]["run_id"] == created["run_id"]
