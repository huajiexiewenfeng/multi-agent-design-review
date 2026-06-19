# Multi-Agent Design Review

Local-first LangGraph workbench for orchestrating multi-agent design reviews with human checkpoints, event logs, and traceable final docs.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
npm --prefix frontend install
```

## Run Backend

```bash
npm run backend:dev
```

This uses `python -m uvicorn` so it works even when the `uvicorn` console script is not on `PATH`.

## Run Frontend

```bash
npm run frontend:dev
```

## Local CLI Runners

The Web UI can show and select `codex`, `claude-code`, and `antigravity` runners. If the expected local executables are found, the backend auto-registers command templates. You can override any template with an environment variable before starting the backend:

```powershell
$env:MADR_CODEX_COMMAND = '"C:\Users\<you>\AppData\Roaming\npm\codex.cmd" exec --cd "{workspace}" --sandbox read-only -o "{output_file}" - < "{prompt_file}"'
$env:MADR_CLAUDE_CODE_COMMAND = 'type "{prompt_file}" | "C:\Users\<you>\AppData\Roaming\npm\claude.cmd" -p --output-format text > "{output_file}"'
$env:MADR_ANTIGRAVITY_COMMAND = '"D:\soft\Antigravity\bin\antigravity.cmd" chat --mode agent - < "{instruction_file}"'
```

The command may use `{run_id}`, `{agent_id}`, `{stage}`, `{prompt_file}`, `{output_file}`, `{instruction_file}`, and `{workspace}`. Codex CLI and Claude Code are treated as headless output-file runners. Antigravity is currently treated as a launch-and-wait runner: it receives an instruction file that includes the expected output path, and the Web UI shows the handoff until the file appears in `runs/<run_id>/inbox/<agent>/`.

Logs are stored in `runs/<run_id>/runner_logs/<agent_id>/`.

## Test

```bash
npm run backend:test
npm --prefix frontend test -- --run
```

## MVP Storage

Runs are stored under `runs/<run_id>/`. The facts are `events.jsonl` and files. `run.json` is a recomputed projection.
