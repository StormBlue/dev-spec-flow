---
name: dev-spec-flow
description: Spec-driven full-stack development workflow (OpenSpec-style). Activate whenever the user describes something to build — a feature, system, app, page, API, refactor, or non-trivial fix — vague or detailed, small or huge. Triggers on "帮我做/实现/开发/搭建/添加 X", "我想做一个…", "build/implement/add/create/refactor X", "需要一个 X", or any description of something to build. Scales by size — small tasks take a light path, big ones get full specs + multi-round parallel-agent review — so it is not heavyweight by default. Turns fuzzy requirements into living specs (openspec/specs) plus a per-change proposal/spec/design/tasks folder, then runs a no-stop dev loop and parallel, context-isolated code review, and archives the change back into the specs. Skip ONLY for trivial one-liners (rename a variable, fix a typo, change one string).
---

# dev-spec-flow — 规范驱动的全栈开发工作流

把用户那种粗犷、发散的需求，变成**活文档（`openspec/specs/`）+ 一次改动的提案/规格/设计/任务**，再按任务循环开发、并行隔离审核、归档回真相源。**目标是少返工、少遗漏、少中途停顿**。

设计取向：**按体量缩放**——小任务走轻量道（fluid not rigid），大任务才上全套规格与多轮审核；artifact 之间是「使能」不是「闸门」，发现错了随时回头改。

## 何时触发

只要用户在描述一个要构建/修改的东西就触发，无论描述多模糊：

- "帮我做个聊天应用 / 实现文件上传 / 搭个后台 / 重构支付流程"
- "我想做一个 X / 需要一个 Y / 添加 Z 功能"
- "build / implement / add / create / refactor [X]"

**不要触发**：仅一两行的琐碎改动（改变量名、修 typo、调一个字符串）——开销不划算。介于"一行改动"和"做个系统"之间的，**走 Lite 级**，别因为怕重而不用。

## 文档模型

本工作流的文档落在 `openspec/` 下，分两块（完整说明见 [`references/openspec-model.md`](references/openspec-model.md)）：

- **`openspec/specs/`** — 真相源，描述系统**当前**行为（Requirement + Scenario）。只在归档时更新。
- **`openspec/changes/<id>/`** — 一次改动的全部上下文：`proposal.md` + `specs/`（delta）+ `design.md`（可选）+ `tasks.md`。

## 6 阶段总览

```
Phase 0  定级立项   → 轻量判 Lite/Std/Full + 建 change 文件夹，向用户确认级别
Phase 1  调研       → context7 / 可用 skill / WebSearch / 读代码 + 读 openspec/specs/
Phase 2  写文档     → proposal → spec(delta) → design(按需) → tasks（带需求追溯）
Phase 3  开发循环   → 每任务: 改状态→实现→自检→测试→备注→commit→下一个；里程碑验证+push
Phase 4  并行审核   → 隔离子 agent 并行跑各视角，主 agent 聚合去重并修复
Phase 5  归档       → merge delta 回 openspec/specs/，change 移入 archive/
```

**审批闸按级缩放**（开发循环与审核内部都不停）：

| 级别 | 必写 artifact | 审批闸 | 审核（Phase 4） |
|------|---------------|--------|------------------|
| **Lite（小）** | proposal(精简) + 轻量 delta spec + tasks | **1 道**：proposal+tasks 合并过一次 | 1 轮综合（1-2 个并行 agent） |
| **Standard（中）** | proposal + spec + tasks，design 按需 | **2 道**：调研摘要 / 文档 | 一波 4-5 视角并行 agent |
| **Full（超大）** | 全套，可能多个 change | **2-3 道**：调研 / 文档 / 里程碑检查点 | 2-3 波 8-12 视角并行 agent |

---

## Phase 0 — 定级立项

**先轻量定级，别在调研前给死估算。** 粗判即可，调研后（Phase 1 末）再敲定：

- **量级**：Lite / Standard / Full（判据见上表与 [`openspec-model.md`](references/openspec-model.md) 第六节）。
- **粗估规模**：任务数量级（如"约 8 个任务"）、涉及哪些域 / 大致影响面。**不报"人天"**——AI 的人天估算无意义，用相对复杂度。

然后：

1. 起一个 change-id（kebab-case，动词起头，如 `add-team-todo`）。
2. 建 `openspec/changes/<id>/` 文件夹。
3. 一句话报给用户：「我判这是 **Standard** 级（约 N 个任务，涉及 auth/api/ui），按规范走 2 道闸 + 一波并行审核，确认吗？」拿到确认再进 Phase 1。

> Lite 级可以把 Phase 0 的确认和 Phase 2 的文档确认合并成一次，不必单独停。

## Phase 1 — 调研

**目标**：基于业界最新最佳实践给方案，不靠可能过时的训练记忆。完整策略见 [`references/research.md`](references/research.md)。

工具优先级：

1. **context7 MCP**（如可用）——拉库/框架/SDK 最新文档：`resolve-library-id` → `get-library-docs`。**永远不要**靠记忆写版本敏感的 API。
2. **当前可用的 skill**——**先看自己手头实际加载了哪些 skill**（不要假设某个一定在）。如有相关的（前端设计、Claude API、Figma、安全审计等）优先用。
3. **WebSearch / WebFetch**——业界模式、相似优秀项目、设计参考（加当前年份限定新鲜度）。
4. **读项目自身**——`README`、`CONTRIBUTING.md`、`AGENTS.md`/`CLAUDE.md`、依赖清单、相似模块，**以及已有的 `openspec/specs/`**（真相源就是最权威的现状）。

产出**技术决策摘要**（选型+理由 / 架构模式 / 风险+缓解 / 留给用户的开放问题）。Standard/Full 让用户确认后进 Phase 2；Lite 可从简。**调研完回头敲定 Phase 0 的级别**。

## Phase 2 — 写文档

把决策落到 `openspec/changes/<id>/`。artifact 顺序与依赖见 [`openspec-model.md`](references/openspec-model.md)，逐个用模板：

1. **`proposal.md`**（[模板](templates/proposal.md)）——why + what changes + capabilities + 范围 + 成功标准 + impact + 开放问题。
2. **`specs/<domain>/spec.md`**（[模板](templates/spec.md)）——delta（ADDED/MODIFIED/REMOVED），每条 `### Requirement:` 用 SHALL/MUST，配 `#### Scenario:`（WHEN/THEN，至少一个）。**非功能需求也写成可测 Requirement**。
3. **`design.md`**（[模板](templates/design.md)）——**仅复杂时写**（跨模块/新依赖/安全/迁移/有歧义）。技术栈+版本、架构图、数据模型、风险都在这。
4. **`tasks.md`**（[模板](templates/tasks.md)）——分层（里程碑→任务→子任务）+ 依赖图 + 状态 emoji + 备注块，**每个任务标注它实现哪条 Requirement**。

**闭环自查**（[详见](references/openspec-model.md) 第七节）：写完 tasks 后确认——每条 Requirement 都有 ≥1 个任务覆盖了吗？

文档写完**带用户过一遍**（Lite 可与 Phase 0 合并为一次确认），确认后进 Phase 3。

## Phase 3 — 开发循环

完整规则见 [`references/dev-rules.md`](references/dev-rules.md)。**开始前先建 feature 分支**（不直接在共享分支上做，见 [`git-flow.md`](references/git-flow.md)）。

**9 条铁律**摘要：① 严守项目开发规范 ② 类型安全是底线 ③ 依赖锁最新固定版（Rust 例外）④ 注释跟项目主语言（无则中文，解释「为什么」）⑤ 超长文件里程碑后拆分 ⑥ 文档实时更新 ⑦ UI 必先调研设计（[`ui-design.md`](references/ui-design.md)）⑧ **测试是一等公民**——验收 scenario 要落成自动化测试（[`verification.md`](references/verification.md)）⑨ 不中途停下等指令。

### 单任务循环

```
对每个任务 T：
  1. tasks.md 把 T 状态改 🚧
  2. 实现 T，遵守 9 铁律
  3. 自检（references/code-review.md 五项清单）
  4. 写/跑该任务对应的测试（scenario → 测试用例）
  5. 写 T 的备注块（问题 / 实现 / 决策）
  6. tasks.md 把 T 状态改 ✅
  7. commit（单任务粒度；push 见下）
  8. 立刻继续下一个任务，不停下来等指令
```

- **里程碑边界**：一个里程碑全部 ✅ 后，跑**增量验证**（真跑 app / 跑测试套件，可用 `/verify` `/run`，见 [`verification.md`](references/verification.md)），扫超长文件，然后 **push**（每任务 commit 但不必每任务 push；Full 级里程碑后可设检查点向用户汇报）。
- **断点续做**：会话中断或上下文压缩后，**重读 `tasks.md`，从第一个非 ✅ 任务继续**（详见 [`context-and-agents.md`](references/context-and-agents.md)）。
- **只在四种情况停**：真正的需求歧义需拍板 / 外部决策（选型、密钥）/ 破坏性操作授权 / 测试编译反复修不动。用户明说过"AI 老在完成一个任务后停下来要督促"——所以**默认不停**。

## Phase 4 — 并行审核

所有任务 ✅ 后，跑**并行隔离审核**（机制见 [`references/review-agents.md`](references/review-agents.md)，playbook 见 [`references/final-review.md`](references/final-review.md)）。

**核心思想**：不要用写了一肚子代码的主上下文去自审（有偏见、会"我写的应该没问题"）。改为**并发派发多个只读子 agent，每个一个独立干净的上下文、专攻一个视角**（功能正确性 / 类型 & 静态 / 性能 / 安全 / UX & a11y / 跨模块集成 / 回归 / 文档对齐…）。子 agent 看不到主对话历史，判断不被污染。

```
主 agent ──并发派发──► [功能 agent] [安全 agent] [性能 agent] [类型 agent] ...
                          │（各自独立上下文，拿 spec/scenario 当对照基准，只读审查）
                          ▼
主 agent ◄──回传 findings── 聚合 / 去重 / 按 P0/P1/P2 分级 ──► 逐条修复 + 写报告 + commit
```

- 视角数与波数按级缩放（见上表 / final-review）。功能 agent 必须拿 spec 的 **scenario 列表逐条核对**。
- 可调用内置 `/code-review`（自身多 agent、可 `--fix`）、`/security-review`、`/simplify`、`/verify` 作为补充。
- 每波/每视角产出报告 `openspec/changes/<id>/review-<perspective>.md`（[模板](templates/review-report.md)），每波单独 commit。
- **风险驱动，不是凑数**：0 发现也如实记一句，但不要为了填表制造噪音 finding。
- **Codex 降级**：无子 agent 时，按视角**顺序**跑单上下文审查（最好分多次会话以减小污染），见 review-agents.md 末尾。

## Phase 5 — 归档

change 全部 ✅ 且审核通过后（详见 [`openspec-model.md`](references/openspec-model.md) 第八节）：

1. 把 change `specs/` 里的 ADDED/MODIFIED/REMOVED **merge 进 `openspec/specs/<domain>/spec.md`**（主 spec 是干净的非 delta 列表）。
2. `changes/<id>/` 移到 `changes/archive/<YYYY-MM-DD>-<id>/`。
3. 通读 merge 后的 spec 校验无冲突，commit。

向用户汇报：本 change 的全部产出 + specs 更新了什么。

---

## 上下文与原生能力

- **续做真相源**：`tasks.md`（状态 emoji）和 `openspec/` 落盘，是跨会话/抗压缩的真相源。原生 **TodoWrite** 适合「本次会话的即时执行清单」，`tasks.md` 适合「持久的、可断点续做的状态」——两者分工，`tasks.md` 为准。详见 [`context-and-agents.md`](references/context-and-agents.md)。
- **审批闸用 Plan Mode**：Phase 1/2 的确认可借 Plan Mode（只读探索 + 用户批准）落地。
- **省上下文**：长流程里，调研与审核都尽量丢给子 agent 跑（隔离上下文、只回传结论），主线程别被淹。

## 结构索引

```
dev-spec-flow/
├── SKILL.md                       ← 你正在看（Claude Code 入口）
├── AGENTS.md                      ← Codex 入口（内容一致，审核给降级方案）
├── README.md                      ← 安装与使用
├── references/
│   ├── openspec-model.md          ← specs/changes/归档 + Requirement/Scenario + 分级【地基】
│   ├── research.md                ← 调研策略与工具优先级
│   ├── dev-rules.md               ← 9 条铁律展开
│   ├── code-review.md             ← 单任务自检清单
│   ├── verification.md            ← 运行时验证 + 测试即任务
│   ├── git-flow.md                ← 分支 / commit / push 约定
│   ├── review-agents.md           ← 并行隔离审核 agent 机制【新】
│   ├── final-review.md            ← 终审 playbook（用并行 agent）
│   └── ui-design.md               ← UI 设计前置调研
└── templates/
    ├── proposal.md                ← 提案模板【新】
    ├── spec.md                    ← delta 规格模板【新】
    ├── design.md                  ← 技术设计模板【新】
    ├── tasks.md                   ← 任务列表模板
    └── review-report.md           ← 审核报告模板
```

## 一句话哲学

需求来自人类、常常模糊；把它变成**活的规格 + 一次改动的完整上下文**，按体量选最轻够用的严格度，按任务一口气走到底，每步留痕（commit、备注、审核报告），用与上下文隔离的并行 agent 把缺漏审出来，最后归档回真相源。不追银弹，追**少返工、少遗漏、少中途停顿**。
