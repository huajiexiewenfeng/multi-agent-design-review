# Multi-Agent Design Review

Local-first multi-agent design review workbench. It coordinates Architect, Engineer, Reviewer, Synthesizer, and Human roles through a file-first workflow, LangGraph orchestration, event logs, and a Web UI that shows the whole discussion as a traceable timeline.

The current MVP is optimized for a single local user who runs local agent CLIs such as Codex CLI, Claude Code, and Antigravity, while keeping all run data on disk.

## What It Does

- Creates review runs from a requirement title and Markdown requirement text.
- Runs a fixed staged workflow: requirement, clarification, clarified requirement, draft, review, revision, synthesis, final output.
- Shows agent messages, imported files, attachments, runner logs, and final outputs in the Web UI.
- Lets humans answer agent questions in natural language. You do not need to write JSON.
- Lets humans approve final generation explicitly. Final docs are not generated until human approval is saved.
- Lets humans reopen discussion after synthesis with a change request, creating the next review/revision/synthesis round.
- Stores the truth on disk: `events.jsonl`, versioned agent artifacts, Markdown human inputs, and final files.

## Project Shape

```text
backend/   FastAPI API, LangGraph workflow nodes, state projection, runner services
frontend/  React + Vite Web UI
runs/      Local run data, ignored by git
docs/      Planning and design notes
```

Each run is stored under `runs/<run_id>/`. Important files include:

- `events.jsonl`: append-only event log.
- `input/requirement.md`: original requirement.
- `input/human_answers.md`: natural-language human answers.
- `input/clarified_requirement.md`: human-confirmed clarified requirement.
- `input/final_approval.md`: final approval gate.
- `agents/<agent>/...vN.md`: versioned agent artifacts.
- `output/design_doc.md`, `output/execution_doc.md`, `output/transcript.md`: finalized outputs.

`run.json` is only a recomputed projection for UI/API convenience. The durable truth is the files plus `events.jsonl`.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
npm --prefix frontend install
```

## Run Locally

Start the backend:

```bash
npm run backend:dev
```

Start the frontend in another terminal:

```bash
npm run frontend:dev
```

Open:

```text
http://127.0.0.1:5173/
```

## Basic Web UI Flow

1. Create a run from the left sidebar with a title and Markdown requirement.
2. Open Agent settings and choose the local runner plus model for each role.
3. Click Run Until Pause.
4. When the workflow pauses for human input, answer directly in natural language.
5. Save the clarified requirement when the clarification stage is ready.
6. Continue Run Until Pause through draft, review, revision, and synthesis.
7. Inspect the Final Outputs panel.
8. If the synthesized result is acceptable, save final approval and generate final docs.
9. If it needs more work, use Request changes to reopen the discussion and run another round.

The main center area is the conversation timeline. Agent artifacts can be opened from the timeline instead of digging through runner logs.

## Local CLI Runners

The Web UI supports these runner ids:

- `codex`
- `claude-code`
- `antigravity`
- `mock`
- `manual`
- `file`

Each agent has two separate settings:

- Runner: which local CLI or runner type to use.
- Model: the visible model/name passed to that runner when supported.

The app can auto-detect common local CLI paths. You can override command templates with environment variables before starting the backend:

```powershell
$env:MADR_CODEX_COMMAND = '"C:\Users\<you>\AppData\Roaming\npm\codex.cmd" exec --cd "{workspace}" --sandbox read-only -o "{output_file}" - < "{prompt_file}"'
$env:MADR_CLAUDE_CODE_COMMAND = 'type "{prompt_file}" | "C:\Users\<you>\AppData\Roaming\npm\claude.cmd" -p --output-format text --tools "" --safe-mode > "{output_file}"'
$env:MADR_ANTIGRAVITY_COMMAND = '"D:\soft\Antigravity\bin\antigravity.cmd" chat --mode agent - < "{instruction_file}"'
$env:MADR_RUNNER_TIMEOUT_SECONDS = '180'
```

Templates may use:

- `{run_id}`
- `{agent_id}`
- `{stage}`
- `{prompt_file}`
- `{output_file}`
- `{instruction_file}`
- `{workspace}`

Codex CLI and Claude Code are treated as headless output-file runners when their commands support it. Antigravity is currently treated as a launch-and-wait runner: the app creates an instruction file with the expected output path, then waits for a file to appear in `runs/<run_id>/inbox/<agent>/`.

Use Test model in Agent settings to run a smoke test. A successful smoke test output contains:

```text
MADR_RUNNER_SMOKE_OK
```

Runner logs are stored in:

```text
runs/<run_id>/runner_logs/<agent_id>/
```

## Human Input Rules

Human answers are Markdown-first:

- The UI accepts natural language.
- The backend saves it to `input/human_answers.md`.
- `input/human_answers.json` may still be written as a compatibility artifact, but it is not something users need to edit.

Final generation is approval-gated:

- Synthesis can produce draft final documents.
- Final output generation requires `input/final_approval.md`.
- Request changes removes prior approval and creates a new discussion request for the next version.

## Test

Backend:

```bash
pytest backend\tests -q
```

Frontend:

```bash
npm --prefix frontend test -- --run
```

Frontend production build:

```bash
npm --prefix frontend run build
```

## Current MVP Notes

- LangGraph is orchestration only. It is not the truth source.
- The filesystem and `events.jsonl` are the durable protocol.
- The Web UI is the intended control surface.
- Runner integration depends on the local CLI capabilities installed on your machine.
- This project is intentionally local-first before adding hosted collaboration features.
