# Runner E2E Control

flow_id: runner-e2e-control

## Why

The workbench already supports local runners and one LangGraph step at a time, but the user goal is to operate the whole multi-agent flow from the Web UI. Requiring repeated manual clicks for every graph step makes the runner integration feel unfinished and makes mixed Codex CLI / Claude Code / Antigravity CLI runs harder to verify.

## What Changes

- Add a Web UI control that runs the workflow repeatedly until it reaches a meaningful pause point.
- Keep the existing single-step control for precise debugging.
- Stop the loop when human input, runner handoff output, runner failure, final synthesis readiness, or a safety step limit is reached.
- Record successful runner execution events so Codex CLI and Claude Code participation can be proven from `events.jsonl`.
- Add a mixed-run verification report that checks final docs and runner evidence for Codex CLI, Claude Code, and Antigravity.

## Non-Goals

- Do not claim Antigravity is a fully headless runner unless the local CLI writes the expected output file.
- Do not replace the file-first truth source or `events.jsonl` projection model.
- Do not add multi-user queues or a persistent background worker service in this change.

## Acceptance Criteria

- Backend exposes a run-until-pause job that repeatedly calls the existing graph step path.
- The job reports why it stopped and how many steps ran.
- Frontend shows a `Run Until Pause` control and polls it like existing graph jobs.
- Frontend shows mixed-run verification evidence for final outputs and each local runner.
- Existing graph step, runner handoff, runner smoke, and finalize behavior continue to pass tests.

## Active Scope

- `backend/app/services/job_service.py`
- `backend/app/api.py`
- `frontend/src/api/client.ts`
- `frontend/src/components/RunControls.tsx`
- `frontend/src/pages/RunListPage.tsx`
- Runner and workflow tests needed to prove the control loop.
- `backend/app/services/flow_verification_service.py`
- `frontend/src/components/FlowVerificationPanel.tsx`

## Verification Plan

- Add backend tests for run-until-pause stop reasons.
- Add frontend component/page tests for the new control.
- Add backend and frontend tests for mixed runner verification evidence.
- Run the full backend test suite, frontend test suite, and frontend build.
- Exercise the Web UI in the in-app browser against a local run.

## Flow Record

| Step | Status | Evidence |
| --- | --- | --- |
| Requirement anchor | done | This file |
| Implementation | done | Added run-until-pause control, runner success evidence, mixed-run verification API, and Web UI panel |
| Verification | done | Backend targeted tests pass; live mixed run `20260619_202705_a9f6` completed with Codex CLI and Claude Code `runner_succeeded` evidence, Antigravity `runner_waiting` handoff evidence, final docs ready, and no runner/validation failures |
| Archive | pending | Commit and push |
