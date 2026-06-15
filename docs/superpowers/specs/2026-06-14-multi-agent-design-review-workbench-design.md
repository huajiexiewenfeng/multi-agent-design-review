# Multi-Agent Design Review Workbench MVP Design

## 1. 背景

本项目要构建一个本地优先的多 Agent 设计评审工作台。它面向个人使用起步，但按真实开源系统来设计，后续可以扩展为可部署的 Web 服务。

用户当前主要使用 Codex、Claude Code、Antigravity 等本地 Agent 工具，不希望第一阶段强依赖 LLM API key 或某个 CLI。因此 MVP 的核心不是模型调用，而是定义一套可追溯、可人工介入、可由 Web UI 展示的多 Agent 协作协议。

## 2. 系统定位

第一阶段系统定位为：

**File-first Core + Web UI Shell 的本地多 Agent 设计评审工作台。**

系统负责管理完整的设计评审流程：

- 收集原始需求。
- 让多个 Agent 独立提出澄清问题。
- 让 Human 回答问题。
- 形成澄清后的需求。
- 生成各 Agent 的设计 prompt。
- 接收 Agent 初稿。
- 开放交叉评审。
- 接收修订结果。
- 支持 Human 追加评论和决策。
- 半自动推进流程。
- 最终生成 Design Doc 和 Execution Doc。
- 保存完整过程记录。

第一阶段使用 LangGraph 作为后端 workflow engine，并引入 Local Runner abstraction 自动调用本地 Agent。Codex、Claude Code 等本地工具通过 runner 参与流程；Web 粘贴和文件投递作为 fallback。

## 3. 第一阶段范围

### 必须支持

- 本地 Web UI。
- 流程看板视图。
- 聊天时间线视图。
- 回答 AI 澄清问题。
- 粘贴提交 Agent 输出。
- 文件投递 Agent 输出。
- Local Runner 自动调用本地 Agent。
- LangGraph 固定流程编排。
- Human 追加评论和决策。
- Agent 原文不可变。
- 阶段共享规则。
- 半自动流程推进。
- `events.jsonl` 事实日志。
- Markdown 可读记录。
- 本地 `runs/<run_id>/` 工作目录。
- 最低限度内容校验，避免空文件或明显错误格式推进流程。

### 暂不支持

- 强依赖 OpenAI、Claude 或其他 LLM API。
- 强依赖某一个特定 CLI。MVP 提供 runner abstraction，具体本地 Agent runner 可以逐步实现。
- 登录、多用户、权限。
- 远程部署。
- 多人实时协同。
- Human 直接修改 Agent 原始发言。
- 多轮无限 review/revision 循环。
- Agent 输出质量自动评分或复杂 schema 校验。

## 4. 核心原则

### File-first

所有 run 的事实状态保存在本地文件系统。Web UI、LangGraph nodes、Local Runners 和 fallback 文件投递都通过同一套目录和文件协议协作。

### Human-in-the-loop

Human 在需求阶段和执行阶段都可以介入。第一阶段采用检查点模式：系统判断材料齐全后提示可以推进，但最终由 Human 点击确认。

### Agent 原文不可变

Agent 输出一旦提交，作为原始记录保存。Human 不直接修改 Agent 原文，而是追加回答、评论、决策或覆盖性结论。

### 阶段共享

Draft 阶段各 Agent 隔离，不读取其他 Agent 的初稿。进入 Cross Review 阶段后，系统开放所有初稿供交叉评审。

### Web UI 是体验入口，不是唯一真相

Web UI 负责展示、提交和推进流程。系统事实源仍然是 `run.json`、`events.jsonl` 和 run 目录中的 Markdown 文件。

### LangGraph 是编排器，不是真相源

LangGraph 负责把 Requirement、Clarification、Draft、Review、Revision、Synthesis、Finalize 等阶段组织成可恢复的 workflow。LangGraph state 只保存运行所需的轻量引用，例如 `run_id`、当前阶段、参与 Agent 和下一步动作。完整内容、原始输出和审计记录仍然写入 run 目录。

MVP 不把 LangGraph checkpoint 当作最终数据源。即使 checkpoint 丢失，也应能通过 `run.json`、`events.jsonl` 和文件内容恢复 run 的可读状态。

### 单写入入口

所有系统写入都必须经过后端 workflow service。Web UI 提交、文件投递导入、阶段推进和最终导出都使用同一套写入服务，并按 run 维度加锁，避免 `events.jsonl` 追加、文件写入和状态计算之间产生竞态。

## 5. 流程阶段

MVP 固定 7 个阶段。

### 5.1 Requirement

用户创建 run，填写标题和原始需求。系统写入：

- `runs/<run_id>/input/requirement.md`
- `runs/<run_id>/run.json`
- `runs/<run_id>/events.jsonl`

### 5.2 Clarification

LangGraph 的 Clarification node 为 Architect、Engineer、Reviewer 生成澄清 prompt，并通过对应 Local Runner 自动调用本地 Agent。各 Agent 独立阅读原始需求并提出澄清问题。

Human 在 Web UI 中统一回答这些问题。系统保存：

- `agents/<agent>/clarification_questions.md`
- `input/clarification_questions.json`
- `input/human_answers.json`
- `input/human_answers.md`

`clarification_questions.json` 和 `human_answers.json` 按 question id 结构化保存，便于 Web UI 精确展示问题与答案的对应关系。Markdown 文件作为人类可读导出。

### 5.3 Clarified Requirement

Clarified Requirement 阶段是 Human checkpoint。系统展示原始需求、Agent 问题和 Human 回答，并提供可编辑模板。Human 编辑并确认 `input/clarified_requirement.md` 后，LangGraph workflow 才继续进入 Draft Design。

`input/clarified_requirement.md` 是进入 Draft Design 阶段的权威需求输入。

### 5.4 Draft Design

LangGraph 的 Draft node 为 Architect 和 Engineer 生成 draft prompt，并通过对应 Local Runner 自动调用本地 Agent。两个 Agent 在隔离上下文中各自产出设计初稿。

Draft 阶段 prompt 不包含其他 Agent 的 draft。每个 Agent 的结果保存到：

- `agents/<agent>/draft_response.md`

Reviewer 默认不参与 Draft Design。Reviewer 的职责是在 Cross Review 阶段提供专职评审，而不是作为第三个设计方案竞争者。后续用户可以通过 `agents.yaml` 增加其他参与 draft 的角色。

### 5.5 Cross Review

LangGraph 的 Cross Review node 在阶段切换后生成 review prompt。此时系统开放所有初稿，Architect 和 Engineer 互评对方初稿，Reviewer 对所有初稿提供专职评审。

Review 输出保存到：

- `agents/<agent>/review_response.md`

Review 内容需要明确关联被评审的 Agent 或方案。

### 5.6 Revision

LangGraph 的 Revision node 为 Architect 和 Engineer 生成 revision prompt，并通过对应 Local Runner 自动调用本地 Agent。两个 Agent 读取自己收到的评审意见、Human 评论和 Human 决策，提交修订版。

Revision 输出保存到：

- `agents/<agent>/revision_response.md`

Human 可以在该阶段追加执行建议、优先级调整和最终偏好。

### 5.7 Synthesis

Synthesizer 与其他 Agent 一样走 prompt 到 response 的提交流程。LangGraph 的 Synthesis node 生成 synthesis prompt，并通过 Synthesizer runner 自动调用本地 Agent。

系统生成 `agents/synthesizer/synthesis_prompt.md`，runner 将结果写入：

- `agents/synthesizer/synthesis_response.md`

Finalize 时，系统从 `synthesis_response.md` 单向拆分或拷贝生成最终交付物：

- `output/design_doc.md`
- `output/execution_doc.md`
- `output/transcript.md`

其中 `output/` 是最终交付物的唯一权威位置。`agents/synthesizer/synthesis_response.md` 是 Synthesizer 原始输出记录，不作为最终交付物真相源。

## 6. 状态推进规则

每个阶段都有 required inputs。系统根据文件和事件判断当前阶段是否材料齐全。

状态建议：

- `not_started`
- `in_progress`
- `waiting_input`
- `ready_to_advance`
- `completed`

推进规则：

- 系统自动判断当前阶段所需材料是否齐全。
- 材料齐全且通过最低限度内容校验后，将阶段标记为 `ready_to_advance`。
- Human 点击确认后才进入下一阶段。
- 每次阶段变化写入 `events.jsonl`。
- 如果材料不齐，Web UI 显示缺少哪些 Agent 输出或 Human 输入。

最低限度内容校验只防止明显错误，不评价方案质量：

- 文件必须存在且非空。
- Markdown 输出必须包含该阶段要求的二级标题。
- `human_answers.json` 必须覆盖所有 required questions。
- `synthesis_response.md` 必须包含 `# Design Document` 和 `# Execution Document`。

缺席处理：

- MVP 默认要求该阶段必需参与者全部提交。
- 如果某个 Agent 缺席，Human 可以在 Web UI 中显式标记 `skipped` 并填写原因。
- 被 skip 的 Agent 不再阻塞当前阶段，但 skip 事件必须写入 `events.jsonl`。

MVP 不做多轮无限循环，固定流程为：

```text
Requirement -> Clarification -> Clarified Requirement -> Draft Design -> Cross Review -> Revision -> Synthesis
```

## 7. 数据目录协议

每次运行生成独立目录：

`run_id` 使用时间戳加随机后缀，避免同一秒创建多个 run 时冲突。例如 `20260614_180000_a7f3`。

```text
runs/<run_id>/
  run.json
  graph_state.json
  events.jsonl
  runners.yaml

  input/
    requirement.md
    clarification_questions.json
    clarification_questions.md
    human_answers.json
    human_answers.md
    clarified_requirement.md

  agents/
    architect/
      clarification_questions.md
      draft_prompt.md
      draft_response.md
      review_prompt.md
      review_response.md
      revision_prompt.md
      revision_response.md

    engineer/
      clarification_questions.md
      draft_prompt.md
      draft_response.md
      review_prompt.md
      review_response.md
      revision_prompt.md
      revision_response.md

    reviewer/
      clarification_questions.md
      draft_prompt.md
      draft_response.md
      review_prompt.md
      review_response.md
      revision_prompt.md
      revision_response.md

    synthesizer/
      synthesis_prompt.md
      synthesis_response.md

  human/
    comments.md
    decisions.md

  inbox/
    architect/
    engineer/
    reviewer/
    synthesizer/

  runner_logs/
    architect/
    engineer/
    reviewer/
    synthesizer/

  output/
    design_doc.md
    execution_doc.md
    transcript.md
```

目录规则：

- `run.json` 保存 run 元信息和当前状态。
- `graph_state.json` 保存 LangGraph 对当前 run 的轻量执行状态快照，便于 Web UI 展示和故障排查。
- `runners.yaml` 保存当前 run 使用的 Agent 到 runner 的绑定。
- `events.jsonl` 是事实日志。
- `agents/<agent>/` 保存每个 Agent 的 prompt 和输出。
- `human/` 保存 Human 追加内容。
- `inbox/` 保存外部文件投递。后端扫描后导入到对应 `agents/<agent>/` 文件，导入成功后写入事件。
- `runner_logs/` 保存本地 Agent runner 的命令、退出码、stdout/stderr 摘要和错误信息。
- `output/` 保存最终交付物。
- Web UI 粘贴提交和文件投递最终都落到同一批文件，并写入同一种事件。

文件投递规则：

- 外部工具不直接写 `agents/<agent>/` 下的权威 response 文件。
- 外部工具将结果放入 `inbox/<agent>/`。
- 后端 workflow service 负责校验、加锁、复制到目标 response 文件、追加事件和刷新阶段状态。
- 如果目标 response 已存在，导入会创建 corrected submission 或要求 Human 明确覆盖策略，MVP 默认不覆盖原文。

Runner 规则：

- 每个 Agent 通过 `runners.yaml` 绑定一个 runner。
- Runner 读取对应 prompt 文件，并只能写入指定 response 文件或 runner 日志。
- Runner 不直接推进阶段；阶段推进由 LangGraph node 完成校验后触发。
- Runner 失败时写入 `runner_failed` 事件，Web UI 展示错误并允许 Human 重试、切换 runner、手动提交或 skip。
- Manual 和 file runner 是 fallback，不是主路径。

## 8. 事件日志协议

`events.jsonl` 每行一条事件。事件结构建议：

```json
{
  "id": "evt_20260614_180000_001",
  "run_id": "20260614_180000_a7f3",
  "timestamp": "2026-06-14T18:00:00+08:00",
  "stage": "draft_design",
  "actor": "architect",
  "actor_type": "agent",
  "event_type": "agent_output_submitted",
  "message": "Submitted draft design",
  "related_file": "agents/architect/draft_response.md",
  "visibility": "private_until_review",
  "metadata": {}
}
```

核心字段：

- `id`: 事件唯一标识。
- `run_id`: 所属 run。
- `timestamp`: 事件时间。
- `stage`: 所属阶段。
- `actor`: 事件发起者。
- `actor_type`: `human`、`agent`、`system`。
- `event_type`: 事件类型。
- `message`: 简短描述。
- `related_file`: 关联文件。
- `visibility`: 可见性规则。
- `metadata`: 扩展信息。

常见事件类型：

- `run_created`
- `stage_advanced`
- `prompt_generated`
- `agent_output_submitted`
- `human_answer_submitted`
- `human_comment_added`
- `human_decision_added`
- `file_imported`
- `agent_skipped`
- `validation_failed`
- `finalized`
- `final_docs_generated`

`output/transcript.md` 由系统从 `events.jsonl` 渲染生成。生成时机为 Synthesis finalize，同时后续可在每次事件写入后增量刷新。

## 9. Agent 角色

MVP 默认内置 4 个角色。

### Architect Agent

关注架构边界、模块划分、数据流、扩展性和风险。

### Engineer Agent

关注实现路径、技术选型、任务拆分、依赖关系和工程可行性。

### Reviewer Agent

关注漏洞、遗漏、冲突、复杂度、测试和验收风险。Reviewer 默认不产出设计初稿，专注于 Cross Review。

### Synthesizer Agent

不参与初稿竞争，负责最终整合并输出 Design Doc 和 Execution Doc。

系统保留 `agents.yaml` 配置能力：

```yaml
agents:
  architect:
    display_name: Architect
    role: architecture
    participates_in:
      - clarification
      - draft_design
      - cross_review
      - revision

  engineer:
    display_name: Engineer
    role: implementation
    participates_in:
      - clarification
      - draft_design
      - cross_review
      - revision

  reviewer:
    display_name: Reviewer
    role: critical_review
    participates_in:
      - clarification
      - cross_review

  synthesizer:
    display_name: Synthesizer
    role: synthesis
    participates_in:
      - synthesis
```

## 10. Prompt 协议

Prompt 文件是系统和外部 Agent 的接口。外部 Agent 可以是 Codex、Claude Code、Antigravity，也可以是人工。

### Clarification Prompt

输入：

- 原始需求。
- Agent 角色说明。

输出格式：

```markdown
## Clarification Questions

1. What is the expected target user for the first release?
2. Which constraints are mandatory for the implementation?
3. What output format should be considered successful?

## Assumptions

- The first release runs locally and stores all process data in the run directory.
```

### Draft Prompt

输入：

- 原始需求。
- Human 回答。
- 澄清后的需求。
- 当前 Agent 角色说明。

Draft 阶段不输入其他 Agent 的 draft。

输出格式：

```markdown
## Summary
## Proposed Design
## Modules
## Data Flow
## Risks
## Open Questions
```

### Review Prompt

输入：

- 澄清后的需求。
- 当前 reviewer 的角色说明。
- 所有已提交 draft。
- 对 Architect 和 Engineer，额外包含自己的 draft，用于对比与自检。

输出格式：

```markdown
## Review Summary
## Issues
## Conflicts
## Suggestions
## Questions For Human
```

### Revision Prompt

输入：

- 自己的 draft。
- 收到的 reviews。
- Human comments。
- Human decisions。

输出格式：

```markdown
## Revised Design
## Changes Made
## Remaining Risks
## Implementation Notes
```

### Synthesis Prompt

输入：

- 澄清后的需求。
- 所有 draft。
- 所有 review。
- 所有 revision。
- Human comments。
- Human decisions。

输出：

```markdown
# Design Document

## Architecture

The system uses a file-first workflow core with a local Web UI.

# Execution Document

## Implementation Plan

Build storage, workflow, prompt generation, Web UI, and final exports in sequence.
```

Synthesizer 的输出先保存为 `agents/synthesizer/synthesis_response.md`。系统 finalize 时再从该文件生成 `output/design_doc.md` 和 `output/execution_doc.md`。

## 11. Web UI

MVP Web UI 包含 3 个主页面或主视图。

### 11.1 Run 列表页

显示所有历史 run：

- run 标题。
- 当前阶段。
- 当前状态。
- 创建时间。
- 更新时间。
- 打开 run 入口。
- 新建 run 入口。

新建 run 时填写：

- 标题。
- 原始需求 Markdown。

### 11.2 Run 详情页

核心工作台页面，建议布局：

```text
左侧：阶段看板
中间：当前阶段内容
右侧：聊天时间线 / 文件列表
```

阶段看板包含：

- Requirement
- Clarification
- Clarified Requirement
- Draft Design
- Cross Review
- Revision
- Synthesis

每个阶段展示：

- 未开始。
- 进行中。
- 缺少输入。
- 可推进。
- 已完成。

中间区域按阶段展示不同内容：

- Requirement: 原始需求。
- Clarification: Agent 问题和 Human 回答框。
- Clarified Requirement: 澄清后的需求和确认入口。
- Draft Design: Agent prompt 和提交入口。
- Cross Review: review prompt 和 review 提交入口。
- Revision: 收到的 review、revision 提交入口、Human 评论入口。
- Synthesis: 最终文档和导出入口。

右侧区域包含：

- Timeline: 按时间展示所有事件和发言。
- Files: 展示 run 目录下关键文件。
- 后续可加 Decisions: 只看 Human 决策。

### 11.3 Agent 提交弹窗

用于：

- 查看对应 prompt。
- 复制 prompt 给外部 Agent。
- 粘贴 Agent 输出。

提交后：

- 写入对应 `*_response.md`。
- 写入 `events.jsonl`。
- 刷新阶段状态。
- 如果材料齐全，提示可以进入下一阶段。

## 12. 技术架构

第一阶段建议：

```text
Frontend: React + Vite + TypeScript
Backend: Python FastAPI
Storage: Local filesystem
Workflow Engine: LangGraph
Workflow Services: Python service layer
Runner Layer: Local Runner abstraction
```

后端建议结构：

```text
backend/
  app/
    main.py
    models.py
    services/
      run_service.py
      event_service.py
      workflow_service.py
      graph_service.py
      runner_service.py
      prompt_service.py
      file_service.py
      validation_service.py
    graph/
      state.py
      nodes.py
      edges.py
      checkpoints.py
    runners/
      base.py
      codex.py
      claude_code.py
      manual.py
      file.py
    templates/
      prompts/
        clarification.md
        draft.md
        review.md
        revision.md
        synthesis.md
```

前端建议结构：

```text
frontend/
  src/
    pages/
      RunListPage.tsx
      RunDetailPage.tsx
    components/
      StageBoard.tsx
      Timeline.tsx
      AgentPanel.tsx
      MarkdownViewer.tsx
      SubmitOutputDialog.tsx
      HumanInputPanel.tsx
    api/
      client.ts
    types/
      run.ts
```

第一阶段引入 LangGraph，但只用于 workflow orchestration。FastAPI 负责 API，service layer 负责文件写入、事件追加、校验和 runner 调用，LangGraph nodes 通过这些 service 完成每个阶段。

MVP 的 LangGraph 使用边界：

- 使用固定线性图表达阶段流转。
- 使用 interrupt/checkpoint 表达人类确认点。
- 使用 node 封装 prompt generation、runner execution、validation 和 finalize。
- 不把 LangGraph checkpoint 作为唯一事实源。
- 不在 MVP 中实现复杂条件路由或无限循环。

## 13. MVP 里程碑

### M1: Core Storage + API

- 创建 run。
- 读取 run。
- 写入 `run.json`。
- 写入 `graph_state.json`。
- 写入 `events.jsonl`。
- 阶段状态计算。
- 按 run 维度串行化写入。
- 最低限度内容校验。
- 半自动推进 API。

### M2: LangGraph Workflow + Runner

- 定义 LangGraph state、nodes 和固定阶段 edges。
- 实现 Human checkpoint / resume。
- 实现 runner abstraction。
- 实现 codex runner 和 manual/file fallback。
- 生成 clarification、draft、review、revision、synthesis prompt。
- Local Runner 自动调用本地 Agent。
- Web UI 粘贴提交 Agent 输出作为 fallback。
- 文件投递从 `inbox/` 导入。
- 记录提交事件。
- 支持显式 skip 缺席 Agent，并记录原因。

### M3: Web UI Workbench

- Run 列表页。
- Run 详情页。
- 阶段看板。
- 当前阶段内容。
- 时间线视图。
- Human 回答澄清问题。
- Human 评论和决策。

### M4: Final Outputs

- Synthesis 阶段。
- 提交 `agents/synthesizer/synthesis_response.md`。
- Finalize 生成 `output/design_doc.md`。
- Finalize 生成 `output/execution_doc.md`。
- 从 `events.jsonl` 渲染 `output/transcript.md`。
- 最终文档查看和导出。

## 14. 验收标准

MVP 完成时应满足：

- 能创建一个需求 run。
- 能通过 LangGraph 启动并推进 run。
- 能生成 3 个 Agent 的澄清问题 prompt，并通过 runner 自动调用本地 Agent。
- 能以 per-question 结构录入 Human 回答。
- 能推进到 Draft Design 阶段。
- 能生成并展示 Architect 和 Engineer 的 draft prompt，并通过 runner 自动调用本地 Agent。
- Reviewer 默认不参与 draft，只参与 Cross Review。
- 能通过 Web 粘贴或 `inbox/` 文件投递导入 Agent 输出作为 fallback。
- 空文件或缺少必需标题的输出不能推进阶段。
- 同一 run 的事件写入、文件导入和状态计算不会并发互相覆盖。
- 能进入 Cross Review、Revision、Synthesis 阶段。
- 能在 Web UI 看到流程看板。
- 能在 Web UI 看到完整聊天时间线。
- 能通过 Synthesizer response finalize 生成最终 Design Doc 和 Execution Doc。
- `output/` 是最终交付物的唯一权威位置。
- 所有过程都能从 `runs/<run_id>` 文件夹复盘。

## 15. 后续扩展

后续可扩展：

- Codex CLI runner。
- Claude Code CLI runner。
- OpenAI-compatible API runner。
- 更完整的 LangGraph checkpoint/replay 管理。
- 多轮 review/revision 循环。
- Agent 输出 schema 校验。
- 评分和质量门禁。
- 多用户和权限。
- 远程部署。
- 团队协同。
- 决策历史和 diff 视图。
