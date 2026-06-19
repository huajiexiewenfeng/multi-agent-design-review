# Workbench UX v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the local multi-agent design review workbench according to `2026-06-19-workbench-ux-v2-design.md` while preserving the existing run, runner, handoff, finalize, and verification behavior.

**Architecture:** Add a frontend view-model layer that converts existing API responses into v2 UI concepts, then replace the current stacked-page layout with a left Runs sidebar, top stage/status area, central conversation stream, and right execution panel. Keep backend APIs unchanged unless final output preview/open actions require a narrow helper.

**Tech Stack:** React 18, TypeScript, Vite, Vitest, Testing Library, existing FastAPI backend, local filesystem run protocol.

---

## File Structure

- Create `frontend/src/viewModels/workbenchViewModel.ts`: pure projection from raw API data to v2 UI state.
- Create `frontend/src/__tests__/workbenchViewModel.test.ts`: tests for stage rail, conversation, queue, human actions, and final outputs projection.
- Create `frontend/src/components/StageProgressRail.tsx`: compact top workflow rail.
- Create `frontend/src/components/RunStatusBar.tsx`: active job, pause, and waiting-human status.
- Create `frontend/src/components/ConversationStream.tsx`: agent/human/system group-chat-style timeline.
- Create `frontend/src/components/RightExecutionPanel.tsx`: Agent Queue, Human Actions, Artifacts/Final Outputs, Debug sections.
- Create `frontend/src/components/AgentSettingsDialog.tsx`: focused runner/model configuration.
- Modify `frontend/src/pages/RunListPage.tsx`: wire v2 layout and view model while reusing existing handlers.
- Modify `frontend/src/components/HumanInputPanel.tsx` or replace it with natural-language forms in right panel/actions.
- Modify `frontend/src/types/run.ts`: add v2 UI types if shared across components.
- Modify `frontend/src/api/client.ts`: add narrow final-output content/open endpoint only if needed.
- Modify `frontend/src/styles.css`: implement shadcn-like calm workbench layout and responsive behavior.
- Add/update component tests under `frontend/src/__tests__/`.

## Task 1: Workbench View Model

**Files:**
- Create: `frontend/src/viewModels/workbenchViewModel.ts`
- Create: `frontend/src/__tests__/workbenchViewModel.test.ts`
- Modify: `frontend/src/types/run.ts`

- [ ] **Step 1: Write failing tests for projection behavior**

Create `frontend/src/__tests__/workbenchViewModel.test.ts` with tests that call `buildWorkbenchViewModel`.

Test cases:

```ts
import { describe, expect, it } from "vitest";
import { buildWorkbenchViewModel } from "../viewModels/workbenchViewModel";

describe("buildWorkbenchViewModel", () => {
  it("maps the current stage into a compact stage rail", () => {
    const viewModel = buildWorkbenchViewModel({
      run: {
        run_id: "run_1",
        stage: "draft_design",
        status: "waiting_input",
        missing_inputs: ["agents/reviewer/review_response.v*.md"],
        agents: []
      },
      events: [],
      artifacts: [],
      runnerHandoffs: [],
      runnerLogs: [],
      flowVerification: null,
      activeJob: null
    });

    expect(viewModel.stageRail.map((stage) => stage.label)).toEqual([
      "Requirement",
      "Clarification",
      "Draft",
      "Review",
      "Revision",
      "Final"
    ]);
    expect(viewModel.stageRail.find((stage) => stage.id === "draft_design")?.state).toBe("blocked");
  });

  it("turns agent output events and artifacts into conversation messages with model names", () => {
    const viewModel = buildWorkbenchViewModel({
      run: {
        run_id: "run_1",
        stage: "draft_design",
        status: "in_progress",
        missing_inputs: [],
        agents: [
          { id: "architect", label: "Architect", runner: "codex", llm_name: "GPT-5.5", stages: ["draft_design"] }
        ]
      },
      events: [
        {
          id: "evt_1",
          actor: "architect",
          actor_type: "agent",
          event_type: "agent_output_submitted",
          message: "Draft submitted",
          stage: "draft_design",
          related_file: "agents/architect/draft_response.v1.md",
          timestamp: "2026-06-19T10:00:00Z"
        }
      ],
      artifacts: [
        {
          path: "agents/architect/draft_response.v1.md",
          kind: "output",
          agent_id: "architect",
          content: "## Proposed Design\nArchitectural plan"
        }
      ],
      runnerHandoffs: [],
      runnerLogs: [],
      flowVerification: null,
      activeJob: null
    });

    expect(viewModel.conversation[0]).toMatchObject({
      actorLabel: "Architect",
      runnerLabel: "Codex",
      llmName: "GPT-5.5",
      body: "## Proposed Design\nArchitectural plan"
    });
  });

  it("exposes human action cards and final output readiness", () => {
    const viewModel = buildWorkbenchViewModel({
      run: {
        run_id: "run_1",
        stage: "synthesis",
        status: "ready_to_advance",
        missing_inputs: ["input/human_answers.json"],
        agents: []
      },
      events: [],
      artifacts: [],
      runnerHandoffs: [],
      runnerLogs: [],
      flowVerification: {
        run_id: "run_1",
        complete: false,
        final_outputs_ready: true,
        final_outputs: [
          { path: "output/design_doc.md", exists: true, non_empty: true, ready: true },
          { path: "output/execution_doc.md", exists: true, non_empty: true, ready: true }
        ],
        runners: []
      },
      activeJob: null
    });

    expect(viewModel.humanActions[0].title).toContain("Human input required");
    expect(viewModel.finalOutputs.map((output) => output.path)).toEqual([
      "output/design_doc.md",
      "output/execution_doc.md",
      "output/transcript.md"
    ]);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
npm.cmd --prefix frontend test -- --run frontend/src/__tests__/workbenchViewModel.test.ts
```

Expected: FAIL because `../viewModels/workbenchViewModel` does not exist.

- [ ] **Step 3: Implement minimal view model**

Create `frontend/src/viewModels/workbenchViewModel.ts` with a pure `buildWorkbenchViewModel` function. Define local UI types or export them if components need them.

Core behavior:

- Map visible stages to Requirement, Clarification, Draft, Review, Revision, Final.
- Treat `cross_review` as visible Review and `synthesis` as visible Final.
- Treat current stage with missing inputs as `blocked`.
- Convert events into conversation messages.
- Prefer artifact content over event message when `event.related_file` matches an artifact.
- Add runner/LLM labels by actor id.
- Build agent queue from `run.agents`.
- Add a human action when `run.missing_inputs` is non-empty.
- Always expose the three expected final outputs; merge readiness from flow verification.

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
npm.cmd --prefix frontend test -- --run frontend/src/__tests__/workbenchViewModel.test.ts
```

Expected: PASS.

## Task 2: Stage Rail And Run Status Bar

**Files:**
- Create: `frontend/src/components/StageProgressRail.tsx`
- Create: `frontend/src/components/RunStatusBar.tsx`
- Test: `frontend/src/__tests__/StageProgressRail.test.tsx`
- Test: `frontend/src/__tests__/RunStatusBar.test.tsx`

- [ ] **Step 1: Write failing component tests**

Write tests that render stage labels, blocked badges, active job messages, and waiting-human messages.

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
npm.cmd --prefix frontend test -- --run frontend/src/__tests__/StageProgressRail.test.tsx frontend/src/__tests__/RunStatusBar.test.tsx
```

Expected: FAIL because components do not exist.

- [ ] **Step 3: Implement components**

Implement components using props from `WorkbenchViewModel`. Keep them presentational and callback-free except `onSelectStage`.

- [ ] **Step 4: Run tests and verify pass**

Run the same command. Expected: PASS.

## Task 3: Conversation Stream

**Files:**
- Create: `frontend/src/components/ConversationStream.tsx`
- Test: `frontend/src/__tests__/ConversationStream.test.tsx`

- [ ] **Step 1: Write failing test**

Test that messages render actor, stage, runner/LLM, body, related file, and composer placeholder.

- [ ] **Step 2: Run test and verify failure**

Run:

```powershell
npm.cmd --prefix frontend test -- --run frontend/src/__tests__/ConversationStream.test.tsx
```

Expected: FAIL because component does not exist.

- [ ] **Step 3: Implement component**

Render a scrollable conversation list with agent/human/system message cards and a bottom composer. Do not render runner logs as message bodies.

- [ ] **Step 4: Run test and verify pass**

Run the same command. Expected: PASS.

## Task 4: Right Execution Panel

**Files:**
- Create: `frontend/src/components/RightExecutionPanel.tsx`
- Test: `frontend/src/__tests__/RightExecutionPanel.test.tsx`

- [ ] **Step 1: Write failing test**

Test sections: Agent Queue, Human Action Required, Artifacts, Final Outputs, Debug.

- [ ] **Step 2: Run test and verify failure**

Run:

```powershell
npm.cmd --prefix frontend test -- --run frontend/src/__tests__/RightExecutionPanel.test.tsx
```

Expected: FAIL because component does not exist.

- [ ] **Step 3: Implement component**

Render agent queue rows, action cards, artifact rows, final output buttons, and collapsible debug placeholders. Reuse existing import/check/finalize handlers through props.

- [ ] **Step 4: Run test and verify pass**

Run the same command. Expected: PASS.

## Task 5: Agent Settings Dialog

**Files:**
- Create: `frontend/src/components/AgentSettingsDialog.tsx`
- Test: `frontend/src/__tests__/AgentSettingsDialog.test.tsx`
- Modify: existing `AgentSettingsPanel` tests only if the old panel is removed.

- [ ] **Step 1: Write failing test**

Test opening/closing the dialog, runner selection, LLM name editing, save callback, and smoke-test controls.

- [ ] **Step 2: Run test and verify failure**

Run:

```powershell
npm.cmd --prefix frontend test -- --run frontend/src/__tests__/AgentSettingsDialog.test.tsx
```

Expected: FAIL because component does not exist.

- [ ] **Step 3: Implement component**

Use accessible dialog markup. Keep current agent save and runner smoke callbacks.

- [ ] **Step 4: Run test and verify pass**

Run the same command. Expected: PASS.

## Task 6: Wire V2 Layout Into RunListPage

**Files:**
- Modify: `frontend/src/pages/RunListPage.tsx`
- Modify: `frontend/src/styles.css`
- Test: `frontend/src/__tests__/RunListPage.test.tsx`

- [ ] **Step 1: Write failing page test**

Mock API calls and verify the page renders:

- app header
- left Runs sidebar
- stage progress rail
- central conversation stream
- right execution panel
- settings dialog trigger

- [ ] **Step 2: Run page test and verify failure**

Run:

```powershell
npm.cmd --prefix frontend test -- --run frontend/src/__tests__/RunListPage.test.tsx
```

Expected: FAIL because v2 layout is not wired.

- [ ] **Step 3: Refactor page**

Use `buildWorkbenchViewModel` after data loads. Replace stacked panels in the center with the v2 shell. Keep all existing handler functions working.

- [ ] **Step 4: Run page test and verify pass**

Run the same command. Expected: PASS.

## Task 7: Natural-Language Human Inputs

**Files:**
- Modify: `frontend/src/components/HumanInputPanel.tsx` or replace with action form inside `RightExecutionPanel`
- Modify: tests for human answer behavior

- [ ] **Step 1: Write failing test**

Test that human answers can be submitted from natural-language fields without entering raw JSON.

- [ ] **Step 2: Run test and verify failure**

Run:

```powershell
npm.cmd --prefix frontend test -- --run frontend/src/__tests__/HumanInputPanel.test.tsx frontend/src/__tests__/RightExecutionPanel.test.tsx
```

Expected: FAIL for the new natural-language behavior.

- [ ] **Step 3: Implement input behavior**

Keep backend `saveClarificationAnswers(runId, answers)` contract. Convert visible natural-language input into `Record<string, string>` in the UI before submit.

- [ ] **Step 4: Run tests and verify pass**

Run the same command. Expected: PASS.

## Task 8: Full Verification

**Files:**
- Modify docs only if behavior changes from plan.

- [ ] **Step 1: Run frontend unit tests**

Run:

```powershell
npm.cmd --prefix frontend test -- --run
```

Expected: PASS.

- [ ] **Step 2: Run frontend build**

Run:

```powershell
npm.cmd --prefix frontend run build
```

Expected: PASS.

- [ ] **Step 3: Run backend tests if backend changed**

Run:

```powershell
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 4: Browser verification**

Open `http://127.0.0.1:5173/` and verify:

- left Runs sidebar
- top stage rail
- central conversation
- right Agent Queue/Human Actions/Final Outputs
- Agent settings dialog
- existing run controls still trigger jobs

## Self-Review Notes

- Spec coverage: the plan covers layout, state visibility, conversation, natural-language human input, final outputs, settings dialog, debug demotion, and current functionality preservation.
- Placeholder scan: no TODO/TBD placeholders are used as implementation instructions.
- Scope control: backend changes are avoided unless final output preview/open behavior proves impossible with existing APIs.
