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

## Test

```bash
npm run backend:test
npm --prefix frontend test -- --run
```

## MVP Storage

Runs are stored under `runs/<run_id>/`. The facts are `events.jsonl` and files. `run.json` is a recomputed projection.
