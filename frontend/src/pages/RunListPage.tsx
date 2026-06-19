import { type FormEvent, useEffect, useState } from "react";
import {
  createRun,
  finalizeRun,
  getEvents,
  getFlowVerification,
  getRun,
  getGraphJob,
  getRunners,
  getRunnerHandoffs,
  getRunnerLogs,
  getRunnerSmokeJob,
  getStageArtifacts,
  importRunnerHandoffs,
  listRuns,
  readRunFile,
  saveClarificationAnswers,
  saveClarifiedRequirement,
  skipAgent,
  startGraphStepJob,
  startRunUntilPauseJob,
  startRunnerSmokeJob,
  submitAgentOutput,
  updateAgentConfig
} from "../api/client";
import { AgentSettingsDialog } from "../components/AgentSettingsDialog";
import { ConversationStream } from "../components/ConversationStream";
import { FlowVerificationPanel } from "../components/FlowVerificationPanel";
import { RightExecutionPanel } from "../components/RightExecutionPanel";
import { RunControls } from "../components/RunControls";
import { RunStatusBar } from "../components/RunStatusBar";
import { RunnerHealthPanel } from "../components/RunnerHealthPanel";
import { RunnerHandoffsPanel } from "../components/RunnerHandoffsPanel";
import { RunnerLogsPanel } from "../components/RunnerLogsPanel";
import { StageProgressRail } from "../components/StageProgressRail";
import { StageDetailPanel } from "../components/StageDetailPanel";
import type {
  FlowVerification,
  GraphJob,
  RunnerHandoff,
  RunnerHealth,
  RunnerLog,
  RunnerSmokeJob,
  RunnerSmokeResult,
  RunProjection,
  StageArtifact,
  TimelineEvent
} from "../types/run";
import {
  buildWorkbenchViewModel,
  type FinalOutputItem,
  type HumanActionItem
} from "../viewModels/workbenchViewModel";

export function RunListPage() {
  const [runs, setRuns] = useState<RunProjection[]>([]);
  const [selectedRun, setSelectedRun] = useState<RunProjection | null>(null);
  const [title, setTitle] = useState("Demo requirement");
  const [requirement, setRequirement] = useState("# Requirement\nDescribe the feature here.");
  const [statusMessage, setStatusMessage] = useState("");
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [selectedStage, setSelectedStage] = useState("requirement");
  const [stageArtifacts, setStageArtifacts] = useState<StageArtifact[]>([]);
  const [activeJob, setActiveJob] = useState<GraphJob | null>(null);
  const [runnerHealth, setRunnerHealth] = useState<RunnerHealth[]>([]);
  const [runnerHandoffs, setRunnerHandoffs] = useState<RunnerHandoff[]>([]);
  const [runnerLogs, setRunnerLogs] = useState<RunnerLog[]>([]);
  const [flowVerification, setFlowVerification] = useState<FlowVerification | null>(null);
  const [runnerSmokeResults, setRunnerSmokeResults] = useState<Record<string, RunnerSmokeResult>>({});
  const [runnerSmokeJobs, setRunnerSmokeJobs] = useState<Record<string, RunnerSmokeJob>>({});
  const [testingRunnerId, setTestingRunnerId] = useState<string | null>(null);
  const [isImportingHandoffs, setIsImportingHandoffs] = useState(false);
  const [finalOutputPreviews, setFinalOutputPreviews] = useState<Record<string, string>>({});

  useEffect(() => {
    getRunners().then(setRunnerHealth);
    listRuns().then((loadedRuns) => {
      setRuns(loadedRuns);
      setSelectedRun(loadedRuns[0] ?? null);
      if (loadedRuns[0]) {
        getEvents(loadedRuns[0].run_id).then(setEvents);
        getFlowVerification(loadedRuns[0].run_id).then(setFlowVerification);
        getRunnerHandoffs(loadedRuns[0].run_id).then(setRunnerHandoffs);
        getRunnerLogs(loadedRuns[0].run_id).then(setRunnerLogs);
        setSelectedStage(loadedRuns[0].stage);
        getStageArtifacts(loadedRuns[0].run_id, loadedRuns[0].stage).then(setStageArtifacts);
      }
    });
  }, []);

  async function selectRun(run: RunProjection) {
    setSelectedRun(run);
    setSelectedStage(run.stage);
    setFinalOutputPreviews({});
    setEvents(await getEvents(run.run_id));
    setFlowVerification(await getFlowVerification(run.run_id));
    setRunnerHandoffs(await getRunnerHandoffs(run.run_id));
    setRunnerLogs(await getRunnerLogs(run.run_id));
    setStageArtifacts(await getStageArtifacts(run.run_id, run.stage));
  }

  async function selectStage(stage: string) {
    setSelectedStage(stage);
    if (!selectedRun) {
      setStageArtifacts([]);
      return;
    }
    setStageArtifacts(await getStageArtifacts(selectedRun.run_id, stage));
  }

  async function handleCreateRun(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const created = await createRun(title, requirement);
    setRuns((current) => [created, ...current]);
    setSelectedRun(created);
    setSelectedStage(created.stage);
    setEvents(await getEvents(created.run_id));
    setFlowVerification(await getFlowVerification(created.run_id));
    setRunnerHandoffs(await getRunnerHandoffs(created.run_id));
    setRunnerLogs(await getRunnerLogs(created.run_id));
    setStageArtifacts(await getStageArtifacts(created.run_id, created.stage));
    setStatusMessage("Run created");
  }

  async function handleSaveAgent(agentId: string, update: { runner: string; llm_name: string }) {
    if (!selectedRun) {
      return;
    }
    const updated = await updateAgentConfig(selectedRun.run_id, agentId, update.runner, update.llm_name);
    setSelectedRun(updated);
    setRuns((current) => current.map((run) => (run.run_id === updated.run_id ? updated : run)));
    setEvents(await getEvents(updated.run_id));
    setFlowVerification(await getFlowVerification(updated.run_id));
    setRunnerHandoffs(await getRunnerHandoffs(updated.run_id));
    setRunnerLogs(await getRunnerLogs(updated.run_id));
    setStageArtifacts(await getStageArtifacts(updated.run_id, selectedStage));
    setStatusMessage(`${agentId} config saved`);
  }

  async function handleRunnerSmokeTest(runnerId: string) {
    setTestingRunnerId(runnerId);
    const job = await startRunnerSmokeJob(runnerId);
    setRunnerSmokeJobs((current) => ({ ...current, [runnerId]: job }));
    setStatusMessage(`${runnerId} smoke test queued`);
    void pollRunnerSmokeJob(runnerId, job.id);
  }

  async function pollRunnerSmokeJob(runnerId: string, jobId: string) {
    for (;;) {
      await new Promise((resolve) => window.setTimeout(resolve, 1500));
      const job = await getRunnerSmokeJob(runnerId, jobId);
      setRunnerSmokeJobs((current) => ({ ...current, [runnerId]: job }));
      if (job.status === "queued" || job.status === "running") {
        setStatusMessage(job.message);
        continue;
      }
      if (job.result) {
        setRunnerSmokeResults((current) => ({ ...current, [runnerId]: job.result as RunnerSmokeResult }));
      }
      setTestingRunnerId(null);
      setStatusMessage(`${runnerId} smoke test ${job.status}`);
      return;
    }
  }

  async function handleRunGraphStep() {
    if (!selectedRun) {
      return;
    }
    const job = await startGraphStepJob(selectedRun.run_id, true);
    setActiveJob(job);
    setStatusMessage("Graph job started");
    void pollGraphJob(selectedRun.run_id, job.id);
  }

  async function handleRunUntilPause() {
    if (!selectedRun) {
      return;
    }
    const job = await startRunUntilPauseJob(selectedRun.run_id);
    setActiveJob(job);
    setStatusMessage("Run-until-pause started");
    void pollGraphJob(selectedRun.run_id, job.id);
  }

  async function pollGraphJob(runId: string, jobId: string) {
    for (;;) {
      await new Promise((resolve) => window.setTimeout(resolve, 1500));
      const job = await getGraphJob(runId, jobId);
      setActiveJob(job);
      if (job.status === "queued" || job.status === "running") {
        setStatusMessage(job.message);
        continue;
      }
      if (job.status === "failed") {
        setStatusMessage(job.error ? `Graph job failed: ${job.error}` : "Graph job failed");
        return;
      }
      const updated = job.projection ?? (await getRun(runId));
      setSelectedRun(updated);
      setSelectedStage(updated.stage);
      setRuns((current) => current.map((run) => (run.run_id === updated.run_id ? updated : run)));
      setEvents(await getEvents(updated.run_id));
      setFlowVerification(await getFlowVerification(updated.run_id));
      setRunnerHandoffs(await getRunnerHandoffs(updated.run_id));
      setRunnerLogs(await getRunnerLogs(updated.run_id));
      setStageArtifacts(await getStageArtifacts(updated.run_id, updated.stage));
      if (job.mode === "until_pause") {
        setStatusMessage(`Paused: ${job.stop_reason ?? "unknown"} after ${job.steps_run ?? 0} step(s)`);
      } else {
        setStatusMessage("Graph step completed");
      }
      setActiveJob(null);
      return;
    }
  }

  async function handleFinalize() {
    if (!selectedRun) {
      return;
    }
    const updated = await finalizeRun(selectedRun.run_id);
    setSelectedRun(updated);
    setSelectedStage("synthesis");
    setRuns((current) => current.map((run) => (run.run_id === updated.run_id ? updated : run)));
    setEvents(await getEvents(updated.run_id));
    setFlowVerification(await getFlowVerification(updated.run_id));
    setRunnerHandoffs(await getRunnerHandoffs(updated.run_id));
    setRunnerLogs(await getRunnerLogs(updated.run_id));
    setStageArtifacts(await getStageArtifacts(updated.run_id, "synthesis"));
    setStatusMessage("Final output generated");
  }

  async function handleSubmitOutput(agentId: string, stage: string, content: string) {
    if (!selectedRun) {
      return;
    }
    await submitAgentOutput(selectedRun.run_id, agentId, stage, content);
    const updated = await getRun(selectedRun.run_id);
    setSelectedRun(updated);
    setRuns((current) => current.map((run) => (run.run_id === updated.run_id ? updated : run)));
    setEvents(await getEvents(updated.run_id));
    setFlowVerification(await getFlowVerification(updated.run_id));
    setRunnerHandoffs(await getRunnerHandoffs(updated.run_id));
    setRunnerLogs(await getRunnerLogs(updated.run_id));
    setStageArtifacts(await getStageArtifacts(updated.run_id, stage));
    setStatusMessage(`${agentId} output submitted`);
  }

  async function refreshRun(runId: string, stage: string, message: string) {
    const updated = await getRun(runId);
    setSelectedRun(updated);
    setRuns((current) => current.map((run) => (run.run_id === updated.run_id ? updated : run)));
    setEvents(await getEvents(updated.run_id));
    setFlowVerification(await getFlowVerification(updated.run_id));
    setRunnerHandoffs(await getRunnerHandoffs(updated.run_id));
    setRunnerLogs(await getRunnerLogs(updated.run_id));
    setStageArtifacts(await getStageArtifacts(updated.run_id, stage));
    setStatusMessage(message);
  }

  async function handleImportRunnerHandoffs() {
    if (!selectedRun) {
      return;
    }
    setIsImportingHandoffs(true);
    try {
      const result = await importRunnerHandoffs(selectedRun.run_id);
      const updated = result.projection;
      setSelectedRun(updated);
      setSelectedStage(updated.stage);
      setRuns((current) => current.map((run) => (run.run_id === updated.run_id ? updated : run)));
      setEvents(await getEvents(updated.run_id));
      setFlowVerification(await getFlowVerification(updated.run_id));
      setRunnerHandoffs(await getRunnerHandoffs(updated.run_id));
      setRunnerLogs(await getRunnerLogs(updated.run_id));
      setStageArtifacts(await getStageArtifacts(updated.run_id, updated.stage));
      setStatusMessage(
        result.errors.length > 0
          ? `Checked handoffs: ${result.errors.length} error(s)`
          : `Imported ${result.imported.length} waiting output(s)`
      );
    } finally {
      setIsImportingHandoffs(false);
    }
  }

  async function handleSaveAnswers(answers: Record<string, string>) {
    if (!selectedRun) {
      return;
    }
    await saveClarificationAnswers(selectedRun.run_id, answers);
    await refreshRun(selectedRun.run_id, selectedStage, "Human answers saved");
  }

  async function handleSaveRequirement(content: string) {
    if (!selectedRun) {
      return;
    }
    await saveClarifiedRequirement(selectedRun.run_id, content);
    await refreshRun(selectedRun.run_id, selectedStage, "Clarified requirement saved");
  }

  async function handleSubmitHumanInput(action: HumanActionItem, content: string) {
    if (action.missingInput.includes("clarified_requirement")) {
      await handleSaveRequirement(content);
      return;
    }
    await handleSaveAnswers({ human_response: content });
  }

  async function handleOpenFinalOutput(output: FinalOutputItem) {
    if (!selectedRun) {
      return;
    }
    const file = await readRunFile(selectedRun.run_id, output.path);
    setFinalOutputPreviews((current) => ({ ...current, [file.path]: file.content }));
    setStatusMessage(`Opened ${file.path}`);
  }

  async function handleCopyFinalOutput(output: FinalOutputItem) {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(output.path);
      setStatusMessage(`Copied ${output.path}`);
      return;
    }
    setStatusMessage(`Final output path: ${output.path}`);
  }

  async function handleDownloadFinalOutput(output: FinalOutputItem) {
    if (!selectedRun) {
      return;
    }
    const file =
      finalOutputPreviews[output.path] !== undefined
        ? { path: output.path, content: finalOutputPreviews[output.path] }
        : await readRunFile(selectedRun.run_id, output.path);
    const blob = new Blob([file.content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = file.path.split("/").pop() ?? "output.md";
    link.click();
    URL.revokeObjectURL(url);
    setStatusMessage(`Downloaded ${file.path}`);
  }

  async function handleSkipAgent(agentId: string, stage: string, reason: string) {
    if (!selectedRun) {
      return;
    }
    await skipAgent(selectedRun.run_id, agentId, stage, reason);
    await refreshRun(selectedRun.run_id, stage, `${agentId} skipped`);
  }

  const viewModel = buildWorkbenchViewModel({
    run: selectedRun,
    events,
    artifacts: stageArtifacts,
    runnerHandoffs,
    runnerLogs,
    flowVerification,
    activeJob
  });
  const currentStageLabel =
    viewModel.stageRail.find((stage) => stage.id === selectedRun?.stage)?.label ?? selectedRun?.stage ?? "Requirement";
  const isRunning = activeJob?.status === "queued" || activeJob?.status === "running";

  return (
    <main className="workbench workbench-v2">
      <header className="workbench-header app-header">
        <div>
          <h1>Design Review Workbench</h1>
          <p>Local-first multi-agent review room.</p>
        </div>
        <span className="local-first-badge">Local-first</span>
        <AgentSettingsDialog agents={selectedRun?.agents ?? []} onSave={handleSaveAgent} />
        <RunControls
          disabled={!selectedRun}
          isRunning={isRunning}
          canFinalize={selectedRun?.stage === "synthesis" && (selectedRun?.missing_inputs.length ?? 0) === 0}
          onRunStep={handleRunGraphStep}
          onRunUntilPause={handleRunUntilPause}
          onFinalize={handleFinalize}
        />
      </header>

      <div className="workbench-layout">
        <aside className="run-sidebar" aria-label="Runs">
          <form className="create-run-form" onSubmit={handleCreateRun}>
            <h2>New Run</h2>
            <label>
              Title
              <input value={title} onChange={(event) => setTitle(event.target.value)} />
            </label>
            <label>
              Requirement
              <textarea value={requirement} onChange={(event) => setRequirement(event.target.value)} rows={7} />
            </label>
            <button type="submit">Create Run</button>
          </form>

          <div className="run-list">
            <h2>Runs</h2>
            {runs.length === 0 ? <p>No runs yet.</p> : null}
            {runs.map((run) => (
              <button
                key={run.run_id}
                type="button"
                data-current={selectedRun?.run_id === run.run_id ? "true" : "false"}
                onClick={() => selectRun(run)}
              >
                <span>{run.run_id}</span>
                <strong>{run.stage}</strong>
              </button>
            ))}
          </div>
        </aside>

        <section className="run-workspace run-workspace-v2">
          <StageProgressRail
            stages={viewModel.stageRail}
            selectedStage={selectedStage}
            onSelectStage={selectStage}
          />
          <RunStatusBar
            currentStageLabel={currentStageLabel}
            humanActionCount={viewModel.humanActions.length}
            statusMessage={statusMessage}
            jobStatus={viewModel.jobStatus}
          />
          <ConversationStream messages={viewModel.conversation} />

          <details className="advanced-workflow-tools">
            <summary>Advanced workflow tools</summary>
            <StageDetailPanel
              stage={selectedStage}
              artifacts={stageArtifacts}
              missingInputs={selectedStage === selectedRun?.stage ? selectedRun?.missing_inputs ?? [] : []}
              agents={selectedRun?.agents ?? []}
              onSubmitOutput={handleSubmitOutput}
              onSaveAnswers={handleSaveAnswers}
              onSaveRequirement={handleSaveRequirement}
              onSkipAgent={handleSkipAgent}
            />
          </details>
        </section>

        <div className="workbench-side-column">
          <RightExecutionPanel
            agentQueue={viewModel.agentQueue}
            humanActions={viewModel.humanActions}
            artifacts={viewModel.artifacts}
            finalOutputs={viewModel.finalOutputs}
            finalOutputPreviews={finalOutputPreviews}
            canFinalize={selectedRun?.stage === "synthesis" && (selectedRun?.missing_inputs.length ?? 0) === 0}
            isImportingHandoffs={isImportingHandoffs}
            onFinalize={handleFinalize}
            onImportHandoffs={handleImportRunnerHandoffs}
            onSubmitHumanInput={handleSubmitHumanInput}
            onOpenFinalOutput={handleOpenFinalOutput}
            onCopyFinalOutput={handleCopyFinalOutput}
            onDownloadFinalOutput={handleDownloadFinalOutput}
          />
          <details className="debug-tools">
            <summary>Debug tools</summary>
            <RunnerHandoffsPanel
              handoffs={runnerHandoffs}
              isImporting={isImportingHandoffs}
              onImport={handleImportRunnerHandoffs}
            />
            <RunnerLogsPanel logs={runnerLogs} />
            <FlowVerificationPanel verification={flowVerification} />
            <RunnerHealthPanel
              runners={runnerHealth}
              smokeResults={runnerSmokeResults}
              smokeJobs={runnerSmokeJobs}
              testingRunnerId={testingRunnerId}
              onSmokeTest={handleRunnerSmokeTest}
            />
          </details>
        </div>
      </div>
    </main>
  );
}
