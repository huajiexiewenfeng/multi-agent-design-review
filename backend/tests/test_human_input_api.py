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


def test_save_clarification_answers_accepts_natural_language_content(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(
        f"/api/runs/{created['run_id']}/clarification/answers",
        json={"content": "Use Codex and Claude from the Web UI."},
    )

    assert response.status_code == 200
    run_dir = tmp_path / created["run_id"]
    assert "Use Codex and Claude" in (run_dir / "input" / "human_answers.md").read_text(encoding="utf-8")
    assert "human_response" in (run_dir / "input" / "human_answers.json").read_text(encoding="utf-8")


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


def test_approve_final_output(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()

    response = client.post(
        f"/api/runs/{created['run_id']}/final-approval",
        json={"content": "Approved for final generation."},
    )

    assert response.status_code == 200
    run_dir = tmp_path / created["run_id"]
    assert "Approved" in (run_dir / "input" / "final_approval.md").read_text(encoding="utf-8")
    assert "final_output_approved" in (run_dir / "events.jsonl").read_text(encoding="utf-8")


def test_request_discussion_changes_records_next_round(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api_module, "RUNS_ROOT", tmp_path)
    client = TestClient(app)
    created = client.post("/api/runs", json={"title": "Demo", "requirement": "# Requirement\nBuild"}).json()
    run_dir = tmp_path / created["run_id"]
    (run_dir / "input" / "clarification_questions.json").write_text('{"questions":[]}', encoding="utf-8")
    (run_dir / "input" / "human_answers.json").write_text('{"answers":{"human_response":"ok"}}', encoding="utf-8")
    (run_dir / "input" / "human_answers.md").write_text("# Human Answers\n\nok\n", encoding="utf-8")
    (run_dir / "input" / "clarified_requirement.md").write_text("# Clarified\nBuild", encoding="utf-8")
    for agent in ["architect", "engineer", "reviewer"]:
        (run_dir / "agents" / agent).mkdir(parents=True, exist_ok=True)
        (run_dir / "agents" / agent / "clarification_questions.v1.md").write_text(
            "## Clarification Questions\n\n1. [required] Q?",
            encoding="utf-8",
        )
        (run_dir / "agents" / agent / "review_response.v1.md").write_text("## Review Summary\nReview", encoding="utf-8")
        if agent != "reviewer":
            (run_dir / "agents" / agent / "draft_response.v1.md").write_text(
                "## Proposed Design\nDraft",
                encoding="utf-8",
            )
            (run_dir / "agents" / agent / "revision_response.v1.md").write_text(
                "## Revised Design\nRevision",
                encoding="utf-8",
            )
    (run_dir / "agents" / "synthesizer").mkdir(parents=True, exist_ok=True)
    (run_dir / "agents" / "synthesizer" / "design_doc.v1.md").write_text("# Design Document", encoding="utf-8")
    (run_dir / "agents" / "synthesizer" / "execution_doc.v1.md").write_text("# Execution Document", encoding="utf-8")
    (run_dir / "input" / "final_approval.md").write_text("Previously approved", encoding="utf-8")

    response = client.post(
        f"/api/runs/{created['run_id']}/discussion/request-changes",
        json={"content": "Please revisit the design risks."},
    )

    assert response.status_code == 200
    assert not (run_dir / "input" / "final_approval.md").exists()
    assert "Please revisit" in (
        run_dir / "input" / "discussion_requests" / "request_changes.v2.md"
    ).read_text(encoding="utf-8")
    assert "discussion_reopened" in (run_dir / "events.jsonl").read_text(encoding="utf-8")
    assert response.json()["stage"] == "cross_review"
