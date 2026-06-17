import json
from pathlib import Path
import shutil


def _latest_version(path: Path, pattern: str) -> Path:
    candidates = sorted(path.glob(pattern))
    if not candidates:
        raise FileNotFoundError(f"Missing synthesis output matching {pattern}")
    return candidates[-1]


def _render_transcript(events_jsonl: Path) -> str:
    lines = ["# Transcript", ""]
    for raw in events_jsonl.read_text(encoding="utf-8").splitlines():
        if raw.strip() == "":
            continue
        event = json.loads(raw)
        lines.append(f"- **{event.get('actor', 'unknown')}** `{event.get('event_type', 'event')}`: {event.get('message', '')}")
    lines.append("")
    return "\n".join(lines)


def finalize_run(run_dir: Path) -> None:
    synthesizer_dir = run_dir / "agents" / "synthesizer"
    output_dir = run_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    design_source = _latest_version(synthesizer_dir, "design_doc.v*.md")
    execution_source = _latest_version(synthesizer_dir, "execution_doc.v*.md")

    shutil.copyfile(design_source, output_dir / "design_doc.md")
    shutil.copyfile(execution_source, output_dir / "execution_doc.md")
    (output_dir / "transcript.md").write_text(_render_transcript(run_dir / "events.jsonl"), encoding="utf-8")
