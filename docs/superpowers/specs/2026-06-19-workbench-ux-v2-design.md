# Workbench UX v2 Design

Date: 2026-06-19

Status: Proposed

Reference baseline:

- User-provided v2 mockup: Design Review Workbench with left Runs sidebar, top stage progress, central agent conversation, and right execution panel.
- Current implementation: `RunListPage` with `RunControls`, `StageBoard`, `StageDetailPanel`, `RunnerLogsPanel`, `RunnerHandoffsPanel`, `FlowVerificationPanel`, `RunnerHealthPanel`, `AgentSettingsPanel`, and `Timeline`.
- UI direction: shadcn-style calm workbench, Radix-like accessible overlays, Ant Design-like information density for operational panels.

## 1. Product Goal

The v2 workbench should let the human operate the whole multi-agent design review flow from the Web UI without reading local files or runner logs during the normal path.

The main mental model is:

> A design review run is a group conversation with a visible workflow state, an agent queue, human action items, and final output files.

The UI must make three things obvious at all times:

1. What stage the run is in.
2. What the agents and human have said so far.
3. What the human should do next.

## 2. Problems To Fix

The current UI proves the backend flow can run, but it fails as a product surface.

### P1. Main Operation Flow Is Hard To Understand

The current center column requires vertical scrolling through many operational panels. The user cannot quickly tell which panel matters for the current step.

v2 fix:

- Use a stable three-column workbench.
- Keep primary actions in a fixed top command bar.
- Keep only the conversation as the center workspace.
- Move secondary/debug panels to the right panel or drawers.

### P2. Agent Output Is Hidden In Logs And Files

The user wants a group-chat style window where Architect, Engineer, Reviewer, Human, and Synthesizer speak in order.

v2 fix:

- The central pane becomes `ConversationStream`.
- Agent outputs, human answers, human decisions, runner waiting states, blockers, and finalization events render as conversation messages.
- Logs remain available, but only through an agent detail drawer or debug tab.

### P3. Running State Is Too Vague

Long-running commands currently feel like the app may be stuck.

v2 fix:

- Add `RunStatusBar` in the top command area.
- Show queued/running/succeeded/failed state, current runner, current agent, elapsed time, last job message, and last log excerpt when available.
- Show a clear "Waiting for human" state when the workflow pauses by design.

### P4. Human Answers Should Not Require JSON

Human answers currently require raw JSON and fail late if the shape is wrong.

v2 fix:

- Replace raw JSON input with natural-language answer composer.
- For clarification questions, render per-question answer cards when structured questions exist.
- Also support a single natural-language answer box for mixed or unstructured questions.
- Backend can still persist `human_answers.json`; the UI must hide this format from normal users.

### P5. Final Outputs Are Not Discoverable

After finalize, the user must inspect local folders to find generated files.

v2 fix:

- Add a persistent `FinalOutputsPanel`.
- Show `design_doc.md`, `execution_doc.md`, and `transcript.md` when available.
- Provide preview, open local path, copy path, and download actions.

### P6. Agent Model Settings Are In The Wrong Place

Agent runner/model settings currently sit at the bottom of the main page.

v2 fix:

- Move agent configuration into an `AgentSettingsDialog`.
- Open it from the top command bar or left-bottom workspace settings.
- Show runner, visible LLM name, health, smoke test, and save status per agent.

## 3. v2 Layout

The desktop layout follows the user-provided v2 mockup:

```text
--------------------------------------------------------------------------------+
| AppHeader: logo, product name, local-first badge, primary run actions, settings |
+--------------------+--------------------------------+--------------------------+
| RunsSidebar         | StageProgressRail             | RightExecutionPanel      |
| - search            | - Requirement                 | - Agent Queue           |
| - new run           | - Clarification               | - Human Actions         |
| - run cards         | - Draft                       | - Artifacts/Outputs     |
| - local data hint   | - Review                      | - Debug tabs            |
|                     | - Revision                    |                          |
|                     | - Final                       |                          |
|                     +--------------------------------+                          |
|                     | ConversationStream                                      |
|                     | - agent messages                                      |
|                     | - human messages                                      |
|                     | - blocker cards                                       |
|                     | - file attachments                                    |
|                     | - composer                                            |
+--------------------+--------------------------------+--------------------------+
```

### 3.1 App Header

Purpose:

- Brand the app.
- Communicate local-first behavior.
- Provide global run controls.
- Expose settings without occupying the flow.

Contents:

- Product name: `Design Review Workbench`.
- Badge: `Local-first`.
- Primary button: `Run all agents` or context-specific label.
- Secondary dropdown: step run, run until pause, check runner outputs, finalize.
- `Save workspace` or `Export run` can stay secondary.
- `Agent settings` icon button.
- Overflow menu for debug actions.

### 3.2 Runs Sidebar

Purpose:

- Switch runs quickly.
- Create new runs without crowding the center.

Contents:

- Search input.
- New run button.
- Run cards grouped by date.
- Each card shows title, subtitle/requirement summary, updated time, and progress like `3 / 6`.
- Status color:
  - green: complete
  - blue: in progress
  - orange: blocked/action required
  - gray: pending
  - red: failed
- Bottom area: workspace settings and data stored locally.

New run behavior:

- Click `New run` opens a dialog.
- Dialog fields:
  - title
  - original requirement markdown
  - optional default runner preset
- Creating a run selects it and starts at Requirement.

### 3.3 Stage Progress Rail

Purpose:

- Make workflow position obvious.
- Replace the current bulky `StageBoard` cards with a compact top rail.

Stages:

1. Requirement
2. Clarification
3. Draft
4. Review
5. Revision
6. Final

Mapping:

- Existing `cross_review` maps to visible label `Review`.
- Existing `synthesis` maps to visible label `Final`.
- Existing `clarified_requirement` is not a separate top-level rail item in v2; it is a human checkpoint inside Clarification.

Stage states:

- complete
- in progress
- blocked
- pending
- failed

Each item shows:

- number or check mark
- label
- short state text
- blocker dot when human action is required

### 3.4 Center Conversation Stream

Purpose:

- Make agent collaboration the main experience.
- Replace the current split between events, artifacts, and logs.

Message types:

- `agent_message`: agent output submitted or summarized from an artifact.
- `human_message`: human answer/comment/decision.
- `system_event`: stage advanced, run created, finalize generated.
- `blocker_card`: reviewer or workflow blocker requiring human action.
- `file_attachment`: attached generated markdown file.
- `runner_waiting`: runner created a handoff or waits for external output.
- `runner_failed`: command failed, with retry/switch/manual-submit actions.

Each agent message shows:

- role avatar initial: A/E/R/S/H.
- role label: Architect, Engineer, Reviewer, Synthesizer, Human.
- actor type badge: Agent, Human, System.
- runner and LLM name, e.g. `Codex / GPT-5.5` or `Claude Code / Opus 4.8`.
- stage badge.
- timestamp.
- concise text summary.
- attached files, if any.
- expand/collapse full markdown.

Important rule:

- Runner stdout/stderr should not be shown as the message body.
- Normal user-facing message body comes from the agent response artifact or event summary.
- Logs appear only in debug detail.

Composer:

- Placeholder: `Ask a question or provide additional context...`
- Supports natural-language human input.
- Supports attaching a file later, but file attach is not required for v2.
- Supports action mode based on context:
  - answer questions
  - add comment
  - add decision
  - provide manual agent output

### 3.5 Right Execution Panel

Purpose:

- Show operational state without burying the conversation.
- Answer "what is running", "what needs me", and "where are the files".

Sections:

1. Agent Queue
2. Human Action Required
3. Artifacts / Final Outputs
4. Debug

#### Agent Queue

Each agent row shows:

- role avatar and role name.
- runner and LLM name.
- current task text.
- status badge:
  - pending
  - in progress
  - waiting input
  - blocked
  - complete
  - failed
- actions:
  - retry
  - skip
  - open details

Rows:

- Architect
- Engineer
- Reviewer
- Synthesizer
- Human

Human is shown as an actor in the queue when the workflow waits for human input.

#### Human Action Required

This is the most important right-side section when blocked.

Actions can include:

- answer clarification questions
- confirm clarified requirement
- answer reviewer blockers
- confirm acceptance criteria
- approve finalize
- manually submit agent output
- choose skip reason

Each action card shows:

- action title
- one-line context
- primary button
- optional secondary button

Clicking an action opens an inline panel or dialog with natural-language inputs.

#### Artifacts And Final Outputs

Before finalization:

- Show key artifacts grouped by stage.
- Include file name, agent, stage, update time, and actions.

After finalization:

- Promote `Final Outputs` to the top of this section.
- Show:
  - `design_doc.md`
  - `execution_doc.md`
  - `transcript.md`
- Actions:
  - preview
  - open local file
  - copy path
  - download

`Generate final docs` should be disabled until finalization is valid, with a reason line.

#### Debug

Debug content is hidden by default.

Tabs or drawer:

- Runner Logs
- Runner Handoffs
- Runner Health
- Flow Verification

Debug panels are still valuable, but they are not the primary workflow.

## 4. Interaction Flow

### 4.1 New Run

1. User clicks `New run`.
2. Dialog opens.
3. User enters title and requirement.
4. System creates run.
5. New run selected in sidebar.
6. Conversation stream starts with human requirement message and system run-created event.
7. Primary action becomes `Run all agents`.

### 4.2 Run Until Pause

1. User clicks `Run all agents`.
2. `RunStatusBar` shows queued/running state.
3. Agent Queue marks current agent as in progress.
4. As outputs arrive, messages appear in ConversationStream.
5. If the workflow needs human input, state becomes `Waiting for human`.
6. Human Action Required shows the needed action.

### 4.3 Human Answer

1. User clicks `Provide answer`.
2. A natural-language answer dialog or inline panel opens.
3. If structured questions exist, show one answer field per question plus optional global notes.
4. If structured questions are missing, show a single natural-language answer field.
5. UI validates before submit:
   - non-empty
   - all required visible questions answered
6. Backend saves markdown and structured JSON.
7. ConversationStream shows the human answer as a message.
8. Primary action becomes `Continue`.

### 4.4 Agent Output Review

1. Agent output appears as a message.
2. User can expand full markdown.
3. Attached artifact row is visible inside the message.
4. User can add comment or decision from composer.
5. Debug logs remain one click away but not visible by default.

### 4.5 Finalize

1. When Synthesis is complete, right panel enables `Generate final docs`.
2. User clicks finalize.
3. System writes final files to `output/`.
4. ConversationStream adds a finalization message.
5. `Final Outputs` panel shows preview/open/download actions.

## 5. Data And API Needs

The first v2 implementation should reuse existing APIs where possible, but the UI needs a better projection layer.

### 5.1 Existing API Reuse

Reusable endpoints:

- `GET /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/events`
- `GET /api/runs/{run_id}/stages/{stage}/artifacts`
- `GET /api/runs/{run_id}/runner-logs`
- `GET /api/runs/{run_id}/runner-handoffs`
- `GET /api/runs/{run_id}/verification/mixed-runners`
- `POST /api/runs/{run_id}/graph/until-pause/jobs`
- `GET /api/runs/{run_id}/jobs/{job_id}`
- `POST /api/runs/{run_id}/finalize`
- `POST /api/runs/{run_id}/clarification/answers`
- `POST /api/runs/{run_id}/clarified-requirement`
- `POST /api/runs/{run_id}/agents/{agent_id}/outputs`
- `POST /api/runs/{run_id}/agents/{agent_id}/skip`
- `PATCH /api/runs/{run_id}/agents/{agent_id}`

### 5.2 Needed UI Projection

Create a frontend projection function first:

```ts
type WorkbenchViewModel = {
  run: RunProjection | null;
  stageRail: StageRailItem[];
  conversation: ConversationMessage[];
  agentQueue: AgentQueueItem[];
  humanActions: HumanActionItem[];
  artifacts: WorkbenchArtifact[];
  finalOutputs: FinalOutputItem[];
  jobStatus: WorkbenchJobStatus | null;
};
```

This can be built from existing run projection, events, stage artifacts, runner handoffs, runner logs, and flow verification.

Avoid binding v2 components directly to raw API responses. The UI should consume the view model.

### 5.3 Optional Backend Improvement

After frontend projection proves the model, add one backend endpoint:

```text
GET /api/runs/{run_id}/workbench
```

It returns the same `WorkbenchViewModel` shape and reduces frontend stitching.

This is optional for the first UI pass.

## 6. Component Plan

New or replaced components:

- `WorkbenchShell`
- `AppHeader`
- `RunsSidebar`
- `NewRunDialog`
- `StageProgressRail`
- `RunStatusBar`
- `ConversationStream`
- `ConversationMessageCard`
- `ConversationComposer`
- `RightExecutionPanel`
- `AgentQueuePanel`
- `HumanActionsPanel`
- `ArtifactsPanel`
- `FinalOutputsPanel`
- `DebugDrawer`
- `AgentSettingsDialog`

Existing components to demote or refactor:

- `StageBoard` becomes `StageProgressRail`.
- `Timeline` becomes `ConversationStream`.
- `StageDetailPanel` is split into human actions, artifacts, and manual output dialogs.
- `RunnerLogsPanel` moves into `DebugDrawer`.
- `RunnerHandoffsPanel` moves into `DebugDrawer` and Agent Queue detail.
- `FlowVerificationPanel` moves into `DebugDrawer`.
- `RunnerHealthPanel` moves into `AgentSettingsDialog`.
- `AgentSettingsPanel` becomes `AgentSettingsDialog`.
- `RunControls` becomes top-level command buttons plus `RunStatusBar`.

## 7. Visual Design Rules

The UI should feel like a focused local workbench, not a marketing page.

Rules:

- Use dense but calm spacing.
- Prefer 8px border radius or less.
- Avoid decorative gradients, bokeh, or large empty hero sections.
- Use neutral surfaces, clear borders, and restrained accent colors.
- Use role colors only for fast scanning:
  - Architect: purple
  - Engineer: blue
  - Reviewer: green
  - Synthesizer: orange
  - Human: teal or gray
- Status colors:
  - complete: green
  - running: blue
  - blocked/action required: orange
  - failed: red
  - pending: gray
- Buttons should use icons when the action is familiar:
  - run
  - retry
  - skip
  - settings
  - open file
  - copy
  - download
- Use tooltips for icon-only buttons.
- Avoid nesting cards inside cards; right panel rows can be bordered list items.

## 8. Accessibility And Responsive Behavior

Desktop is the primary target for MVP.

Minimum requirements:

- All actions must be keyboard reachable.
- Dialogs trap focus and return focus on close.
- Status badges must not rely on color alone.
- Text inside buttons and status pills must not overflow.
- Conversation stream and right panel scroll independently.
- Top header and stage rail remain visible during center scroll.

Responsive behavior:

- At narrow widths, RunsSidebar collapses to a drawer.
- RightExecutionPanel collapses to tabs or drawer.
- ConversationStream remains the primary view.

## 9. Implementation Slices

### Slice 1. Layout Shell

- Introduce `WorkbenchShell`.
- Implement three-column layout and fixed app header.
- Move existing data loading into the shell without changing backend behavior.

### Slice 2. Stage Rail And Status Bar

- Replace bulky flow board with `StageProgressRail`.
- Add `RunStatusBar`.
- Make paused/running/waiting states clear.

### Slice 3. Conversation Stream

- Build frontend projection from events and artifacts.
- Render agent and human messages in the center pane.
- Move event timeline out of the right sidebar.

### Slice 4. Right Execution Panel

- Implement Agent Queue.
- Implement Human Action Required.
- Implement Artifacts list.
- Move debug panels behind tabs/drawer.

### Slice 5. Natural-Language Human Inputs

- Replace raw JSON input with natural-language and per-question forms.
- Validate before save.
- Preserve backend JSON persistence.

### Slice 6. Final Outputs

- Add final outputs view.
- Provide preview/open/copy/download actions.
- Make finalize state obvious.

### Slice 7. Agent Settings Dialog

- Move agent configuration into dialog.
- Include runner, LLM name, runner health, smoke test, and save state.

### Slice 8. Polish And Verification

- Add component tests for the new view model and critical panels.
- Run frontend tests.
- Verify desktop screenshot against the v2 mockup.
- Check mobile/narrow behavior for non-overlap.

## 10. Non-Goals

This v2 design does not add:

- Remote multi-user collaboration.
- Authentication.
- Cloud sync.
- New runner types.
- A new backend storage model.
- Agent-to-agent real-time streaming.
- Full markdown editor.

The v2 goal is to make the current local-first workflow usable and product-like.

## 11. Acceptance Criteria

The v2 UI is acceptable when:

- A user can create a run, run agents, answer human checkpoints, finalize, and open final outputs without reading local folders.
- Agent outputs appear in the center conversation stream, not only in logs.
- The current stage and next required human action are visible without scrolling.
- Runner/model names are visible in Agent Queue and agent messages.
- Human answer entry does not require raw JSON.
- Agent settings are opened from a dialog, not displayed at the bottom of the page.
- Runner logs are still available but no longer dominate the normal workflow.
- The page visually follows the user-provided v2 mockup: left run list, top stage rail, central conversation, right execution panel.
