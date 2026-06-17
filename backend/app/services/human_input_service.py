from pathlib import Path

from backend.app.models import ActorType, Stage
from backend.app.services.event_service import append_event
from backend.app.services.file_service import run_lock, write_json, write_text
from backend.app.services.state_service import recompute_state


def save_clarification_answers(run_dir: Path, answers: dict[str, str]):
    with run_lock(run_dir):
        write_json(run_dir / "input" / "human_answers.json", {"answers": answers})
        markdown = ["# Human Answers", ""]
        for question_id, answer in answers.items():
            markdown.append(f"- `{question_id}`: {answer}")
        markdown.append("")
        write_text(run_dir / "input" / "human_answers.md", "\n".join(markdown))
        append_event(
            run_dir,
            Stage.CLARIFIED_REQUIREMENT,
            "human",
            ActorType.HUMAN,
            "human_answer_submitted",
            "Submitted clarification answers",
            "input/human_answers.json",
        )
        projection = recompute_state(run_dir)
        write_json(run_dir / "run.json", projection.model_dump(mode="json"))
        return projection


def save_clarified_requirement(run_dir: Path, content: str):
    with run_lock(run_dir):
        write_text(run_dir / "input" / "clarified_requirement.md", content)
        append_event(
            run_dir,
            Stage.CLARIFIED_REQUIREMENT,
            "human",
            ActorType.HUMAN,
            "clarified_requirement_saved",
            "Saved clarified requirement",
            "input/clarified_requirement.md",
        )
        projection = recompute_state(run_dir)
        write_json(run_dir / "run.json", projection.model_dump(mode="json"))
        return projection
