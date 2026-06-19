from pathlib import Path

from backend.app.models import ActorType, Stage
from backend.app.services.event_service import append_event
from backend.app.services.runner_handoff_service import get_runner_handoffs, import_waiting_runner_outputs


def test_get_runner_handoffs_reads_waiting_instruction(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001"
    log_dir = run_dir / "runner_logs" / "architect"
    log_dir.mkdir(parents=True)
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    (log_dir / "antigravity.log").write_text("waiting for output", encoding="utf-8")
    (log_dir / "antigravity_instruction.md").write_text(
        "\ufeffOUTPUT_FILE: C:/work/run_001/inbox/architect/clarification_result.md\n",
        encoding="utf-8",
    )
    append_event(
        run_dir,
        Stage.CLARIFICATION,
        "architect",
        ActorType.AGENT,
        "runner_waiting",
        "Antigravity launched; waiting for output file",
        "runner_logs/architect/antigravity.log",
        {"runner": "antigravity", "status": "waiting_input"},
    )

    result = get_runner_handoffs(run_dir)

    assert result["handoffs"][0]["agent_id"] == "architect"
    assert result["handoffs"][0]["output_file"] == "C:/work/run_001/inbox/architect/clarification_result.md"
    assert result["handoffs"][0]["instruction_file"] == "runner_logs/architect/antigravity_instruction.md"
    assert "OUTPUT_FILE" in result["handoffs"][0]["instruction"]


def test_import_waiting_runner_outputs_imports_matching_inbox_file(tmp_path: Path) -> None:
    run_dir = tmp_path / "run_001"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("# Requirement\nBuild", encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    inbox = run_dir / "inbox" / "architect"
    inbox.mkdir(parents=True)
    (inbox / "clarification_result.md").write_text(
        "## Clarification Questions\n\n1. [required] What is the goal?\n\n## Assumptions\n\n- Local flow.\n",
        encoding="utf-8",
    )
    append_event(
        run_dir,
        Stage.CLARIFICATION,
        "architect",
        ActorType.AGENT,
        "runner_waiting",
        "Antigravity launched; waiting for output file",
        "runner_logs/architect/antigravity.log",
        {"runner": "antigravity", "status": "waiting_input"},
    )

    result = import_waiting_runner_outputs(run_dir)

    assert result["imported"] == ["agents/architect/clarification_questions.v1.md"]
    assert (run_dir / "agents" / "architect" / "clarification_questions.v1.md").is_file()


def test_import_waiting_runner_outputs_ignores_resolved_handoff(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run_001"
    (run_dir / "input").mkdir(parents=True)
    (run_dir / "input" / "requirement.md").write_text("# Requirement\nBuild", encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    reviewer_dir = run_dir / "agents" / "reviewer"
    reviewer_dir.mkdir(parents=True)
    (reviewer_dir / "clarification_questions.v1.md").write_text(
        "## Clarification Questions\n\n1. [required] What is the goal?\n\n## Assumptions\n\n- Local flow.\n",
        encoding="utf-8",
    )
    append_event(
        run_dir,
        Stage.CLARIFICATION,
        "reviewer",
        ActorType.AGENT,
        "runner_waiting",
        "Antigravity launched; waiting for output file",
        "runner_logs/reviewer/antigravity.log",
        {"runner": "antigravity", "status": "waiting_input"},
    )

    def fail_import(*args, **kwargs):
        raise AssertionError("resolved handoff should not be imported again")

    monkeypatch.setattr(
        "backend.app.services.runner_handoff_service.import_existing_stage_output",
        fail_import,
    )

    result = import_waiting_runner_outputs(run_dir)

    assert result["imported"] == []
    assert result["errors"] == []
