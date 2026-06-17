from fastapi.testclient import TestClient

import backend.app.api as api_module
from backend.app.main import app


def test_get_run_detail_returns_projection(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.get(f"/api/runs/{created['run_id']}")

    assert response.status_code == 200
    assert response.json()["run_id"] == created["run_id"]


def test_skip_agent_writes_event_and_recomputes(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(
        f"/api/runs/{created['run_id']}/agents/reviewer/skip",
        json={"stage": "clarification", "reason": "Not needed for this run"},
    )

    assert response.status_code == 200
    events = client.get(f"/api/runs/{created['run_id']}/events").json()
    assert any(event["event_type"] == "agent_skipped" for event in events)


def test_advance_writes_stage_advanced_event(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(f"/api/runs/{created['run_id']}/advance")

    assert response.status_code == 200
    events = client.get(f"/api/runs/{created['run_id']}/events").json()
    assert any(event["event_type"] == "stage_advanced" for event in events)


def test_revert_writes_stage_reverted_event(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(f"/api/runs/{created['run_id']}/revert", json={"reason": "Need to revise"})

    assert response.status_code == 200
    events = client.get(f"/api/runs/{created['run_id']}/events").json()
    assert any(event["event_type"] == "stage_reverted" for event in events)
