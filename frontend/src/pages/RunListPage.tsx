import { type FormEvent, useEffect, useState } from "react";
import {
  createRun,
  finalizeRun,
  getEvents,
  getRun,
  getGraphJob,
  getRunners,
  getRunnerLogs,
  getRunnerSmokeJob,
  getStageArtifacts,
  listRuns,
  saveClarificationAnswers,
  saveClarifiedRequirement,
  skipAgent,
  startGraphStepJob,
  startRunnerSmokeJob,
  submitAgentOutput,
  updateAgentConfig
} from "../api/client";
import { AgentSettingsPanel } from "../components/AgentSettingsPanel";
import { RunControls } from "../components/RunControls";
import { RunnerHealthPanel } from "../components/RunnerHealthPanel";
import { RunnerLogsPanel } from "../components/RunnerLogsPanel";
import { StageBoard } from "../components/StageBoard";
import { StageDetailPanel } from "../components/StageDetailPanel";
import { Timeline } from "../components/Timeline";
import type {
  GraphJob,
  RunnerHealth,
  RunnerLog,
  RunnerSmokeJob,
  RunnerSmokeResult,
  RunProjection,
  StageArtifact,
  TimelineEvent
} from "../types/run";

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
  const [runnerLogs, setRunnerLogs] = useState<RunnerLog[]>([]);
  const [runnerSmokeResults, setRunnerSmokeResults] = useState<Record<string, RunnerSmokeResult>>({});
  const [runnerSmokeJobs, setRunnerSmokeJobs] = useState<Record<string, RunnerSmokeJob>>({});
  const [testingRunnerId, setTestingRunnerId] = useState<string | null>(null);

  useEffect(() => {
    getRunners().then(setRunnerHealth);
    listRuns().then((loadedRuns) => {
      setRuns(loadedRuns);
      setSelectedRun(loadedRuns[0] ?? null);
      if (loadedRuns[0]) {
        getEvents(loadedRuns[0].run_id).then(setEvents);
        getRunnerLogs(loadedRuns[0].run_id).then(setRunnerLogs);
        setSelectedStage(loadedRuns[0].stage);
        getStageArtifacts(loadedRuns[0].run_id, loadedRuns[0].stage).then(setStageArtifacts);
      }
    });
  }, []);

  async function selectRun(run: RunProjection) {
    setSelectedRun(run);
    setSelectedStage(run.stage);
    setEvents(await getEvents(run.run_id));
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
      setRunnerLogs(await getRunnerLogs(updated.run_id));
      setStageArtifacts(await getStageArtifacts(updated.run_id, updated.stage));
      setStatusMessage("Graph step completed");
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
    setRunnerLogs(await getRunnerLogs(updated.run_id));
    setStageArtifacts(await getStageArtifacts(updated.run_id, stage));
    setStatusMessage(`${agentId} output submitted`);
  }

  async function refreshRun(runId: string, stage: string, message: string) {
    const updated = await getRun(runId);
    setSelectedRun(updated);
    setRuns((current) => current.map((run) => (run.run_id === updated.run_id ? updated : run)));
    setEvents(await getEvents(updated.run_id));
    setRunnerLogs(await getRunnerLogs(updated.run_id));
    setStageArtifacts(await getStageArtifacts(updated.run_id, stage));
    setStatusMessage(message);
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

  async function handleSkipAgent(agentId: string, stage: string, reason: string) {
    if (!selectedRun) {
      return;
    }
    await skipAgent(selectedRun.run_id, agentId, stage, reason);
    await refreshRun(selectedRun.run_id, stage, `${agentId} skipped`);
  }

  return (
    <main className="workbench">
      <header className="workbench-header">
        <div>
          <h1>Multi-Agent Design Review</h1>
          <p>Run the design review flow from one local Web UI.</p>
        </div>
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

        <section className="run-workspace">
          <RunControls
            disabled={!selectedRun}
            isRunning={activeJob?.status === "queued" || activeJob?.status === "running"}
            canFinalize={selectedRun?.stage === "synthesis" && (selectedRun?.missing_inputs.length ?? 0) === 0}
            onRunStep={handleRunGraphStep}
            onFinalize={handleFinalize}
          />
          {statusMessage ? <p className="status-message">{statusMessage}</p> : null}
          <StageBoard
            currentStage={selectedRun?.stage ?? "requirement"}
            agents={selectedRun?.agents}
            missingInputs={selectedRun?.missing_inputs ?? []}
            selectedStage={selectedStage}
            onSelectStage={selectStage}
          />
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
          <RunnerLogsPanel logs={runnerLogs} />
          <RunnerHealthPanel
            runners={runnerHealth}
            smokeResults={runnerSmokeResults}
            smokeJobs={runnerSmokeJobs}
            testingRunnerId={testingRunnerId}
            onSmokeTest={handleRunnerSmokeTest}
          />
          {selectedRun?.agents ? <AgentSettingsPanel agents={selectedRun.agents} onSave={handleSaveAgent} /> : null}
        </section>

        <Timeline events={events} />
      </div>
    </main>
  );
}
