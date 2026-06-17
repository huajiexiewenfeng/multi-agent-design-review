import json
from pathlib import Path
import re


def _extract_questions(content: str) -> list[str]:
    questions: list[str] = []
    for line in content.splitlines():
        match = re.match(r"^\s*\d+\.\s*(.+)$", line)
        if match:
            questions.append(match.group(1).strip())
    return questions


def merge_clarification_questions(run_dir: Path) -> None:
    merged: list[dict[str, object]] = []
    counter = 1
    for path in sorted(run_dir.glob("agents/*/clarification_questions.v*.md")):
        agent = path.parts[-2]
        for question in _extract_questions(path.read_text(encoding="utf-8")):
            required = "[required]" in question.lower()
            clean = question.replace("[required]", "").strip()
            merged.append(
                {
                    "id": f"q_{counter:03d}",
                    "text": clean,
                    "source_agents": [agent],
                    "required": required,
                    "merged_from": [f"{agent}:q{counter}"],
                }
            )
            counter += 1
    input_dir = run_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "clarification_questions.json").write_text(
        json.dumps({"questions": merged}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown = ["# Clarification Questions", ""]
    for item in merged:
        marker = "required" if item["required"] else "optional"
        markdown.append(f"- `{item['id']}` ({marker}) {item['text']}")
    markdown.append("")
    (input_dir / "clarification_questions.md").write_text("\n".join(markdown), encoding="utf-8")
