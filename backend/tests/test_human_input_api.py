from fastapi.testclient import TestClient

import backend.app.api as api_module
from backend.app.main import app


def test_save_clarification_answers(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(
        f"/api/runs/{created['run_id']}/clarification/answers",
        json={"answers": {"q_001": "Local developer"}},
    )

    assert response.status_code == 200
    run_dir = tmp_path / created["run_id"]
    assert "q_001" in (run_dir / "input" / "human_answers.json").read_text(encoding="utf-8")
    assert "Local developer" in (run_dir / "input" / "human_answers.md").read_text(encoding="utf-8")


def test_save_clarified_requirement(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(
        f"/api/runs/{created['run_id']}/clarified-requirement",
        json={"content": "# Clarified Requirement\nUse local files."},
    )

    assert response.status_code == 200
    run_dir = tmp_path / created["run_id"]
    assert "local files" in (run_dir / "input" / "clarified_requirement.md").read_text(encoding="utf-8")
