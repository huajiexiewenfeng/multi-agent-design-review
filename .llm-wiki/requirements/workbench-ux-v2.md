# Workbench UX v2

flow_id: workbench-ux-v2

## Why

The current workbench can run the multi-agent flow, but the user experience is too difficult for normal use. Agent outputs are split between stage artifacts, timeline events, and runner logs. Human answers require JSON. Final output files are not visible in the Web UI. Agent settings are displayed at the bottom of the main page instead of a focused configuration surface.

The product goal is to let the user operate the whole local-first multi-agent design review workflow from the Web UI.

## What Changes

- Rebuild the workbench around the UX v2 spec in `docs/superpowers/specs/2026-06-19-workbench-ux-v2-design.md`.
- Use a three-zone product model: left Runs, center agent/human conversation, right execution panel.
- Add a view-model layer that projects raw run, event, artifact, runner, and verification data into UI-ready state.
- Replace the event-only timeline with a group-chat-style conversation stream.
- Replace raw JSON human answer input with natural-language and per-question forms.
- Show current run status, active job state, waiting-human state, and blockers without requiring log inspection.
- Add visible final output previews/actions for `design_doc.md`, `execution_doc.md`, and `transcript.md`.
- Move agent runner/model configuration into a dialog-style configuration surface.
- Keep runner logs, handoffs, health, and verification accessible as debug tools instead of primary workflow panels.

## Non-Goals

- Do not change the file-first truth model.
- Do not replace the existing backend workflow engine in this UI change.
- Do not add remote multi-user collaboration, authentication, or cloud sync.
- Do not add new runner types as part of the UX v2 work.
- Do not turn the UI into an Ant Design, MUI, or Magic UI clone.

## Acceptance Criteria

- A user can create a run, run agents, answer human checkpoints, finalize, and open final outputs without reading local folders.
- Agent outputs and human inputs appear in a central conversation stream.
- The current stage, running state, and next human action are visible without scrolling through debug panels.
- Runner and LLM names are visible in agent messages and the agent queue.
- Human answer entry does not require raw JSON.
- Final outputs are visible in the Web UI with preview/open/copy/download style actions.
- Agent settings are accessed through a dialog or focused settings surface, not a bottom-of-page panel.
- Runner logs and handoffs remain available for debugging.
- Existing backend runner, handoff, finalize, and verification behavior continues to work.

## Active Scope

- `frontend/src/pages/RunListPage.tsx`
- `frontend/src/types/run.ts`
- `frontend/src/api/client.ts`
- `frontend/src/viewModels/`
- `frontend/src/components/`
- `frontend/src/styles.css`
- `frontend/src/__tests__/`
- Existing FastAPI endpoints only, unless a narrow output-preview/open-file helper is required.

## Read-Only Scope

- `docs/superpowers/specs/2026-06-19-workbench-ux-v2-design.md`
- Existing run data under `runs/`
- Existing runner logs and handoff files

## Verification Plan

- Add frontend unit tests for the workbench view model.
- Add component tests for stage rail, status bar, conversation stream, right execution panel, final outputs, and agent settings dialog.
- Run `npm --prefix frontend test -- --run`.
- Run `npm --prefix frontend run build`.
- Run backend tests if backend endpoints are changed.
- Verify the local Web UI in the in-app browser at `http://127.0.0.1:5173/`.

## Flow Record

| Step | Status | Evidence |
| --- | --- | --- |
| Requirement anchor | done | This file |
| UX spec | done | `docs/superpowers/specs/2026-06-19-workbench-ux-v2-design.md` |
| Implementation plan | done | `docs/superpowers/plans/2026-06-19-workbench-ux-v2-implementation.md` |
| Implementation | done | V2 view model, stage rail, status bar, conversation stream, execution panel, natural-language human input, final output actions, and agent settings dialog |
| Verification | done | Frontend tests, backend tests, production build, and in-app browser verification |
| Archive | pending | Final commit and push |
