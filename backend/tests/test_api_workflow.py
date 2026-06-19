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


def test_get_stage_artifacts_returns_prompt_and_outputs(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()
    run_id = created["run_id"]
    client.post(f"/api/runs/{run_id}/graph/step", json={"confirmed": True})

    response = client.get(f"/api/runs/{run_id}/stages/clarification/artifacts")

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "clarification"
    paths = [artifact["path"] for artifact in body["artifacts"]]
    assert "agents/architect/clarification_prompt.md" in paths
    assert "agents/architect/clarification_questions.v1.md" in paths
    assert body["artifacts"][0]["content"]


def test_get_runner_logs_returns_log_contents(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()
    run_id = created["run_id"]
    run_dir = tmp_path / run_id
    (run_dir / "runner_logs" / "architect").mkdir(parents=True, exist_ok=True)
    (run_dir / "runner_logs" / "architect" / "command.log").write_text("exit_code: 1", encoding="utf-8")

    response = client.get(f"/api/runs/{run_id}/runner-logs")

    assert response.status_code == 200
    assert response.json()["logs"][0]["agent_id"] == "architect"
    assert "exit_code: 1" in response.json()["logs"][0]["content"]


def test_get_runner_handoffs_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    monkeypatch.setattr(
        api_module,
        "get_runner_handoffs",
        lambda run_dir: {"run_id": run_dir.name, "handoffs": [{"agent_id": "architect"}]},
    )
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.get(f"/api/runs/{created['run_id']}/runner-handoffs")

    assert response.status_code == 200
    assert response.json()["handoffs"][0]["agent_id"] == "architect"


def test_import_runner_handoffs_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    monkeypatch.setattr(
        api_module,
        "import_waiting_runner_outputs",
        lambda run_dir: {"projection": {"run_id": run_dir.name}, "imported": ["agents/architect/out.md"], "errors": []},
    )
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(f"/api/runs/{created['run_id']}/runner-handoffs/import")

    assert response.status_code == 200
    assert response.json()["imported"] == ["agents/architect/out.md"]


def test_get_mixed_runner_verification_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    monkeypatch.setattr(
        api_module,
        "get_mixed_runner_verification",
        lambda run_dir: {"run_id": run_dir.name, "complete": True, "runners": []},
    )
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.get(f"/api/runs/{created['run_id']}/verification/mixed-runners")

    assert response.status_code == 200
    assert response.json()["complete"] is True


def test_runner_smoke_test_endpoint_returns_result(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    monkeypatch.setattr(
        api_module,
        "run_runner_smoke_test",
        lambda runner_id, runs_root: {"runner_id": runner_id, "status": "succeeded"},
    )
    client = TestClient(app)

    response = client.post("/api/runners/codex/smoke-test")

    assert response.status_code == 200
    assert response.json()["runner_id"] == "codex"
    assert response.json()["status"] == "succeeded"


def test_runner_smoke_job_endpoints(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)

    class FakeJob:
        id = "smoke_job_1"
        runner_id = "codex"
        status = "queued"
        message = "Runner smoke test queued"

        def model_dump(self, mode="json"):
            return {
                "id": self.id,
                "runner_id": self.runner_id,
                "status": self.status,
                "message": self.message,
                "result": None,
                "error": None,
                "created_at": "2026-06-19T00:00:00+00:00",
            }

    monkeypatch.setattr(api_module, "start_runner_smoke_job", lambda runs_root, runner_id: FakeJob())
    monkeypatch.setattr(api_module, "get_runner_smoke_job", lambda job_id: FakeJob())
    client = TestClient(app)

    created = client.post("/api/runners/codex/smoke-test/jobs")
    fetched = client.get("/api/runners/codex/smoke-test/jobs/smoke_job_1")

    assert created.status_code == 200
    assert created.json()["id"] == "smoke_job_1"
    assert fetched.status_code == 200
    assert fetched.json()["runner_id"] == "codex"


def test_run_until_pause_job_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)

    class FakeJob:
        id = "job_until_pause_1"
        run_id = "run_001"
        status = "queued"
        message = "Run-until-pause queued"
        mode = "until_pause"
        stop_reason = None
        steps_run = 0
        projection = None
        error = None
        started_at = None
        finished_at = None
        created_at = "2026-06-19T00:00:00+00:00"

        def model_dump(self, mode="json"):
            return {
                "id": self.id,
                "run_id": self.run_id,
                "status": self.status,
                "message": self.message,
                "mode": self.mode,
                "stop_reason": self.stop_reason,
                "steps_run": self.steps_run,
                "projection": self.projection,
                "error": self.error,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "created_at": self.created_at,
            }

    monkeypatch.setattr(api_module, "start_run_until_pause_job", lambda runs_root, run_id, max_steps: FakeJob())
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(f"/api/runs/{created['run_id']}/graph/until-pause/jobs", json={"max_steps": 8})

    assert response.status_code == 200
    assert response.json()["mode"] == "until_pause"


def test_finalize_run_endpoint_writes_output_docs_and_event(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()
    run_id = created["run_id"]
    run_dir = tmp_path / run_id
    synth_dir = run_dir / "agents" / "synthesizer"
    synth_dir.mkdir(parents=True, exist_ok=True)
    (synth_dir / "design_doc.v1.md").write_text("# Design Document\n\n## Architecture\nA", encoding="utf-8")
    (synth_dir / "execution_doc.v1.md").write_text("# Execution Document\n\n## Implementation Plan\nB", encoding="utf-8")

    response = client.post(f"/api/runs/{run_id}/finalize")

    assert response.status_code == 200
    assert (run_dir / "output" / "design_doc.md").is_file()
    assert (run_dir / "output" / "execution_doc.md").is_file()
    events = client.get(f"/api/runs/{run_id}/events").json()
    assert any(event["event_type"] == "finalized" for event in events)
    artifacts = client.get(f"/api/runs/{run_id}/stages/synthesis/artifacts").json()["artifacts"]
    paths = [artifact["path"] for artifact in artifacts]
    assert "output/design_doc.md" in paths
    assert "output/execution_doc.md" in paths
