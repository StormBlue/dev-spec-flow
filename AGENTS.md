# dev-spec-flow — 规范驱动的全栈开发工作流

> 这份 AGENTS.md 给 Codex / 其它通过项目根 `AGENTS.md` 自动加载指令的 AI agent 用。Claude Code 用户请参考同目录 `SKILL.md`（内容一致，只多 frontmatter，且并行审核走原生子 agent）。
>
> **引用路径**：下文引用的 `references/...`、`templates/...` 若你按 README「方式一/二」部署到了 `.dev-spec-flow/` 下，请把前缀改成 `.dev-spec-flow/references/...`、`.dev-spec-flow/templates/...`。

把用户那种粗犷、发散的需求，变成**活文档（`openspec/specs/`）+ 一次改动的提案/规格/设计/任务**，再按任务循环开发、审核、归档回真相源。**目标是少返工、少遗漏、少中途停顿**，并**按体量缩放**——小任务走轻量道，大任务才上全套。

---

## 何时启用

只要用户在描述一个要构建/修改的东西就启用，无论多模糊（"帮我做个 X / 实现 Y / 添加 Z / build/implement/refactor …"）。**不启用**：仅一两行的琐碎改动（改变量名、修 typo）。介于两者之间的走 **Lite 级**。

---

## 文档模型（地基）

文档落在 `openspec/`，分两块（完整说明见 `references/openspec-model.md`）：

- **`openspec/specs/`** — 真相源，描述系统**当前**行为（Requirement + Scenario），只在归档时更新。
- **`openspec/changes/<id>/`** — 一次改动的全部上下文：`proposal.md` + `specs/`（delta）+ `design.md`（可选）+ `tasks.md`。

change 完成后**归档**：把 delta merge 进 `specs/`，change 文件夹移入 `changes/archive/`。

---

## 6 阶段总览

```
Phase 0  定级立项   → 轻量判 Lite/Std/Full + 建 change 文件夹，向用户确认级别
Phase 1  调研       → 拉最新文档 / 可用工具 / WebSearch / 读代码 + 读 openspec/specs/
Phase 2  写文档     → proposal → spec(delta) → design(按需) → tasks（带需求追溯）
Phase 3  开发循环   → 每任务: 改状态→实现→自检→测试→备注→commit→下一个；里程碑验证+push
Phase 4  审核       → 按视角审查（Claude Code 并行隔离 agent；Codex 顺序降级）
Phase 5  归档       → merge delta 回 openspec/specs/，change 移入 archive/
```

**审批闸按级缩放**（开发循环与审核内部都不停）：

| 级别 | 必写 artifact | 审批闸 | 审核 |
|------|---------------|--------|------|
| **Lite（小）** | proposal(精简)+轻量 delta spec+tasks | 1 道（合并确认） | 1 视角综合 |
| **Standard（中）** | proposal+spec+tasks，design 按需 | 2 道（调研/文档） | 4-5 视角 |
| **Full（超大）** | 全套，可能多 change | 2-3 道（+里程碑检查点） | 2-3 波 8-12 视角 |

---

## Phase 0 — 定级立项

**先轻量定级，别在调研前给死估算**，调研后再敲定：

- 量级 Lite/Std/Full（判据见 `references/openspec-model.md` 第六节）。
- 粗估任务数量级 + 涉及哪些域。**不报"人天"**（AI 的人天估算无意义）。
- 起 change-id（kebab-case 动词起头，如 `add-team-todo`），建 `openspec/changes/<id>/`。
- 一句话报级别给用户确认。Lite 级可与 Phase 2 文档确认合并成一次。

## Phase 1 — 调研

**基于业界最新最佳实践，不靠可能过时的训练记忆。** 完整策略见 `references/research.md`。

1. **拉最新库/框架文档**——有 context7 MCP 优先用（`resolve-library-id` → `get-library-docs`），没有就 WebFetch 官方文档站。永远不要靠记忆写版本敏感的 API。
2. **当前可用的工具**——先看自己环境实际有什么（别假设），有相关的优先用。
3. **WebSearch / WebFetch**——业界模式、相似项目、设计参考。
4. **读项目自身**——`README`、`CONTRIBUTING.md`、`AGENTS.md`、依赖清单、相似模块，**以及已有的 `openspec/specs/`**。

产出**技术决策摘要**（选型+理由/架构模式/风险+缓解/开放问题），Standard/Full 让用户确认后进 Phase 2。调研完敲定级别。

## Phase 2 — 写文档

落到 `openspec/changes/<id>/`，逐个用模板（顺序与依赖见 `references/openspec-model.md`）：

1. **`proposal.md`**（`templates/proposal.md`）——why + what changes + capabilities + 范围 + 成功标准 + impact + 开放问题。
2. **`specs/<domain>/spec.md`**（`templates/spec.md`）——delta（ADDED/MODIFIED/REMOVED）。每条 `### Requirement:` 用 SHALL/MUST，配 `#### Scenario:`（WHEN/THEN，至少一个，**正好 4 个井号**）。非功能需求也写成可测 Requirement。
3. **`design.md`**（`templates/design.md`）——**仅复杂时写**（跨模块/新依赖/安全/迁移/有歧义）。技术栈+版本、架构图、数据模型、风险在此。
4. **`tasks.md`**（`templates/tasks.md`）——分层+依赖图+状态 emoji+备注块，**每个任务标注实现哪条 Requirement**。

**闭环自查**：每条 Requirement 都有 ≥1 任务覆盖吗？文档带用户过一遍后进 Phase 3。

## Phase 3 — 开发循环

**先建 feature 分支**（见 `references/git-flow.md`）。9 条铁律见 `references/dev-rules.md`：① 严守项目规范 ② 类型安全 ③ 依赖锁最新固定版（Rust 例外）④ 注释跟项目主语言（无则中文，解释「为什么」）⑤ 超长文件里程碑后拆分 ⑥ 文档实时更新 ⑦ UI 必先调研设计 ⑧ **测试是一等公民**（`references/verification.md`）⑨ 不中途停。

### 单任务循环

```
对每个任务 T：
  1. tasks.md 把 T 状态改 🚧
  2. 实现 T，遵守 9 铁律
  3. 自检（references/code-review.md 五项清单）
  4. 写/跑该任务对应的测试（scenario → 测试用例）
  5. 写 T 的备注块（问题/实现/决策）
  6. tasks.md 把 T 状态改 ✅
  7. commit（单任务粒度）
  8. 立刻继续下一个任务，不停下来等指令
```

- **里程碑边界**：全部 ✅ 后跑增量验证（真跑 app + 测试套件）、扫超长文件，然后 **push**（每任务 commit 但不必每任务 push）。
- **断点续做**：中断/上下文压缩后，**重读 `tasks.md`，从第一个非 ✅ 任务继续**（见 `references/context-and-agents.md`）。
- **只在四种情况停**：真正需求歧义 / 外部决策（选型、密钥）/ 破坏性操作授权 / 反复修不动。用户明说过"AI 老停下要督促"——**默认不停**。

## Phase 4 — 审核

所有任务 ✅ 后按视角审查（playbook 见 `references/final-review.md`，机制见 `references/review-agents.md`）。

**核心思想**：不要用写了一肚子代码的开发上下文去自审（有偏见、会"我写的应该没问题"）。要么换隔离上下文，要么换视角，对照 spec 的 scenario 逐条查。

- **Claude Code**：并发派发只读子 agent，每个独立干净上下文专攻一个视角，主 agent 聚合/去重/分级/修复。
- **Codex（降级）**：无子 agent，按视角**顺序**跑——理想情况**每个视角开一次新会话**（或清空上下文重进），只带 change 目录 + diff，人工模拟"隔离上下文"；每个视角开头自我提示"忽略我之前写代码的假设，以新人视角审查"。

视角清单（按级别选 1-2 / 4-5 / 8-12 项）：功能正确性（拿 scenario 逐条核对）/ 类型 & 静态 / 性能 / 安全 / UX & a11y / 跨模块集成 / 回归 / 文档对齐 / 数据 & 迁移 / 运维可观测。详见 `references/review-agents.md` 的清单库与 charter。

每视角产出报告 `openspec/changes/<id>/review-<perspective>.md`（`templates/review-report.md`），修复后重跑测试，commit。**风险驱动不凑数**：0 发现如实记，不编造。

## Phase 5 — 归档

change 全部 ✅ 且审核通过后（见 `references/openspec-model.md` 第八节）：

1. 把 change `specs/` 的 ADDED/MODIFIED/REMOVED **merge 进 `openspec/specs/<domain>/spec.md`**。
2. `changes/<id>/` 移到 `changes/archive/<YYYY-MM-DD>-<id>/`。
3. 通读校验无冲突，commit。向用户汇报全部产出 + specs 更新了什么。

---

## 一句话哲学

把模糊需求变成**活的规格 + 一次改动的完整上下文**，按体量选最轻够用的严格度，按任务一口气走到底，每步留痕（commit、备注、审核报告），换个隔离的视角把缺漏审出来，最后归档回真相源。
