from pathlib import Path


def has_required_headings(path: Path, headings: list[str]) -> bool:
    if not path.is_file():
        return False
    content = path.read_text(encoding="utf-8")
    return all(heading in content for heading in headings)
