from backend.app.models import Stage
from backend.app.services.clarification_service import merge_clarification_questions
from backend.app.services.flow_control_service import run_until_pause
from backend.app.services.human_input_service import save_clarification_answers, save_clarified_requirement
from backend.app.services.run_service import create_run


def test_run_until_pause_stops_for_human_input_after_clarification(tmp_path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild MVP")

    result = run_until_pause(tmp_path, projection.run_id)

    assert result["status"] == "paused"
    assert result["stop_reason"] == "human_input"
    assert result["steps_run"] == 1
    assert result["projection"]["stage"] == Stage.CLARIFIED_REQUIREMENT.value


def test_run_until_pause_reaches_ready_to_finalize_after_human_input(tmp_path) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild MVP")
    run_dir = tmp_path / projection.run_id
    run_until_pause(tmp_path, projection.run_id)
    merge_clarification_questions(run_dir)
    save_clarification_answers(run_dir, {"q_001": "Local developer"})
    save_clarified_requirement(run_dir, "# Clarified Requirement\nLocal developer")

    result = run_until_pause(tmp_path, projection.run_id)

    assert result["stop_reason"] == "ready_to_finalize"
    assert result["steps_run"] == 4
    assert result["projection"]["stage"] == Stage.SYNTHESIS.value
    assert result["projection"]["missing_inputs"] == []


def test_run_until_pause_stops_for_runner_handoff(tmp_path, monkeypatch) -> None:
    projection = create_run(tmp_path, title="Demo", requirement="# Requirement\nBuild MVP")

    monkeypatch.setattr(
        "backend.app.services.flow_control_service.run_graph_step",
        lambda runs_root, run_id, confirmed: {
            "projection": {
                "run_id": run_id,
                "stage": Stage.CLARIFICATION.value,
                "status": "waiting_input",
                "missing_inputs": ["agents/architect/clarification_questions.v*.md"],
            }
        },
    )
    monkeypatch.setattr(
        "backend.app.services.flow_control_service.get_runner_handoffs",
        lambda run_dir: {"handoffs": [{"stage": Stage.CLARIFICATION.value, "agent_id": "architect"}]},
    )

    result = run_until_pause(tmp_path, projection.run_id)

    assert result["stop_reason"] == "runner_handoff"
    assert result["steps_run"] == 1
