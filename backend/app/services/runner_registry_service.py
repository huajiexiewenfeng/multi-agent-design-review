from pathlib import Path
import os
import subprocess


WORKSPACE = Path.cwd()
NPM_BIN = Path.home() / "AppData" / "Roaming" / "npm"


RUNNER_REGISTRY = {
    "codex": {
        "label": "Codex CLI",
        "env": "MADR_CODEX_COMMAND",
        "candidates": [NPM_BIN / "codex.cmd"],
        "version_args": ["--version"],
        "template": '"{executable}" exec --cd "{workspace}" --sandbox read-only -o "{output_file}" - < "{prompt_file}"',
    },
    "claude-code": {
        "label": "Claude Code",
        "env": "MADR_CLAUDE_CODE_COMMAND",
        "candidates": [NPM_BIN / "claude.cmd"],
        "version_args": ["--version"],
        "template": 'type "{prompt_file}" | "{executable}" -p --output-format text > "{output_file}"',
    },
    "antigravity": {
        "label": "Antigravity CLI",
        "env": "MADR_ANTIGRAVITY_COMMAND",
        "candidates": [Path("D:/soft/Antigravity/bin/antigravity.cmd")],
        "version_args": ["--version"],
        "template": '"{executable}" chat --mode agent - < "{instruction_file}"',
    },
}


def resolve_runner_command(runner: str) -> str | None:
    definition = RUNNER_REGISTRY.get(runner)
    if not definition:
        return None
    env_name = str(definition["env"])
    if os.environ.get(env_name):
        return os.environ[env_name]
    executable = _first_existing(definition["candidates"])
    if not executable:
        return None
    return (
        str(definition["template"])
        .replace("{executable}", str(executable))
        .replace("{workspace}", str(WORKSPACE))
    )


def get_runner_health() -> list[dict[str, object]]:
    health: list[dict[str, object]] = []
    for runner, definition in RUNNER_REGISTRY.items():
        executable = _first_existing(definition["candidates"])
        env_command = os.environ.get(str(definition["env"]))
        version, error = _read_version(executable, list(definition["version_args"])) if executable else (None, "not found")
        command_template = env_command or resolve_runner_command(runner)
        health.append(
            {
                "id": runner,
                "label": definition["label"],
                "available": executable is not None and error is None,
                "configured": command_template is not None,
                "executable": str(executable) if executable else None,
                "version": version,
                "env": definition["env"],
                "command_template": command_template,
                "error": error,
            }
        )
    return health


def _first_existing(candidates: object) -> Path | None:
    for candidate in candidates:
        path = Path(candidate)
        try:
            if path.is_file():
                return path
        except OSError:
            continue
    return None


def _read_version(executable: Path, args: list[str]) -> tuple[str | None, str | None]:
    try:
        completed = subprocess.run(
            [str(executable), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except Exception as exc:
        return None, str(exc)
    text = (completed.stdout or completed.stderr).strip()
    if completed.returncode != 0:
        return text or None, f"exit code {completed.returncode}"
    return text.splitlines()[0] if text else None, None
