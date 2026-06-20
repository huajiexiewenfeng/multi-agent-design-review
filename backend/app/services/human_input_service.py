from pathlib import Path
import re

from backend.app.models import ActorType, Stage
from backend.app.services.event_service import append_event
from backend.app.services.file_service import run_lock, write_json, write_text
from backend.app.services.state_service import recompute_state


def save_clarification_answers(run_dir: Path, answers: dict[str, str] | None = None, content: str | None = None):
    with run_lock(run_dir):
        normalized_answers = answers or {"human_response": content or ""}
        human_markdown = _answers_to_markdown(normalized_answers, content)
        write_json(run_dir / "input" / "human_answers.json", {"answers": normalized_answers})
        write_text(run_dir / "input" / "human_answers.md", human_markdown)
        append_event(
            run_dir,
            Stage.CLARIFIED_REQUIREMENT,
            "human",
            ActorType.HUMAN,
            "human_answer_submitted",
            "Submitted clarification answers",
            "input/human_answers.md",
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


def approve_final_output(run_dir: Path, content: str):
    with run_lock(run_dir):
        approval = content.strip() or "Approved"
        write_text(run_dir / "input" / "final_approval.md", approval + "\n")
        append_event(
            run_dir,
            Stage.SYNTHESIS,
            "human",
            ActorType.HUMAN,
            "final_output_approved",
            "Approved final output generation",
            "input/final_approval.md",
        )
        projection = recompute_state(run_dir)
        write_json(run_dir / "run.json", projection.model_dump(mode="json"))
        return projection


def request_discussion_changes(run_dir: Path, content: str):
    with run_lock(run_dir):
        required_version = _next_discussion_version(run_dir)
        request_file = run_dir / "input" / "discussion_requests" / f"request_changes.v{required_version}.md"
        write_text(request_file, content.strip() + "\n")
        approval_file = run_dir / "input" / "final_approval.md"
        if approval_file.exists():
            approval_file.unlink()
        append_event(
            run_dir,
            Stage.SYNTHESIS,
            "human",
            ActorType.HUMAN,
            "discussion_reopened",
            "Requested another discussion round",
            str(request_file.relative_to(run_dir)).replace("\\", "/"),
            {"required_version": required_version},
        )
        projection = recompute_state(run_dir)
        write_json(run_dir / "run.json", projection.model_dump(mode="json"))
        return projection


def _next_discussion_version(run_dir: Path) -> int:
    versions = [1]
    pattern = re.compile(r"^design_doc\.v(\d+)\.md$")
    for path in (run_dir / "agents" / "synthesizer").glob("design_doc.v*.md"):
        match = pattern.match(path.name)
        if match:
            versions.append(int(match.group(1)))
    return max(versions) + 1


def _answers_to_markdown(answers: dict[str, str], content: str | None) -> str:
    if content is not None:
        body = content.strip()
        return f"# Human Answers\n\n{body}\n"

    markdown = ["# Human Answers", ""]
    for question_id, answer in answers.items():
        markdown.append(f"- `{question_id}`: {answer}")
    markdown.append("")
    return "\n".join(markdown)
