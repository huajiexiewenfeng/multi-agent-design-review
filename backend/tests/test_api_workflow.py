from fastapi.testclient import TestClient

import backend.app.api as api_module
from backend.app.main import app


def test_submit_agent_output_imports_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(
        f"/api/runs/{created['run_id']}/agents/architect/submit",
        json={
            "stage": "draft_design",
            "content": "## Summary\nA\n\n## Proposed Design\nB\n\n## Modules\nC\n\n## Data Flow\nD\n\n## Risks\nE\n\n## Open Questions\nF\n",
        },
    )

    assert response.status_code == 200
    assert "draft_response.v1.md" in response.json()["related_file"]


def test_get_events_returns_event_list(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.get(f"/api/runs/{created['run_id']}/events")

    assert response.status_code == 200
    assert response.json()[0]["event_type"] == "run_created"
