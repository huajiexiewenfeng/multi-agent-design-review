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

## Run Frontend

```bash
npm run frontend:dev
```

## Local CLI Runners

The Web UI can show and select `codex`, `claude-code`, and `antigravity` runners. By default they behave like manual runners. To make one run automatically, set a local command template before starting the backend:

```powershell
$env:MADR_CODEX_COMMAND = 'codex exec --full-auto "{prompt_file}"'
$env:MADR_CLAUDE_CODE_COMMAND = 'claude -p "{prompt_file}"'
$env:MADR_ANTIGRAVITY_COMMAND = 'antigravity run "{prompt_file}"'
```

The command may use `{run_id}`, `{agent_id}`, `{stage}`, `{prompt_file}`, and `{output_file}`. If the command writes markdown to stdout, the system imports it as that agent's output. If the command writes directly to `{output_file}`, that file is imported instead. Logs are stored in `runs/<run_id>/runner_logs/<agent_id>/command.log`.

## Test

```bash
npm run backend:test
npm --prefix frontend test -- --run
```

## MVP Storage

Runs are stored under `runs/<run_id>/`. The facts are `events.jsonl` and files. `run.json` is a recomputed projection.
