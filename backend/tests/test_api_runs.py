from fastapi.testclient import TestClient

import backend.app.api as api_module
from backend.app.main import app


def test_create_run_api(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)

    response = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"})

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "clarification"
    assert body["status"] == "waiting_input"
