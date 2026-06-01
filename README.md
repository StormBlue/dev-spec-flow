# dev-spec-flow

一个面向全栈工程的**规范驱动开发工作流** skill：把粗犷的需求描述，变成**活文档（`openspec/specs/`）+ 一次改动的提案/规格/设计/任务**，按任务循环开发、并行隔离审核、归档回真相源。**按体量缩放**——小任务走轻量道，大任务才上全套。同时适配 **Claude Code** 和 **Codex**。

> 文档模型与流程思想融合自 [OpenSpec](https://github.com/Fission-AI/OpenSpec)（specs 真相源 + changes 增量提案 + 归档循环、Requirement/Scenario 行为契约、渐进严格度）。
>
> ```
> Phase 0  定级立项 → 轻量判 Lite/Std/Full + 建 change 文件夹
> Phase 1  调研     → context7 / 可用工具 / WebSearch / 读代码 + 读 openspec/specs/
> Phase 2  写文档   → proposal → spec(delta) → design(按需) → tasks
> Phase 3  开发循环 → 每任务: 开发→自检→测试→备注→commit→下一个；里程碑验证+push
> Phase 4  审核     → 并行隔离审核 agent（各视角防上下文污染）+ 聚合修复
> Phase 5  归档     → merge delta 回 openspec/specs/，change 移入 archive/
> ```

---

## 核心特性

- **OpenSpec 文档模型**：`openspec/specs/`（系统当前行为的真相源）与 `openspec/changes/<id>/`（一次改动的 delta 提案）分离，完成即归档 merge 回真相源——天然适配 brownfield 与并行开发。
- **Requirement / Scenario 行为契约**：用 SHALL/MUST + WHEN/THEN 写需求，每个 scenario 都是可测试用例，打通「需求→测试→审核」闭环。
- **按体量缩放（Lite / Standard / Full）**：审批闸、文档详尽度、审核轮数都随级别缩放，小任务不被仪式拖累。
- **不中途停**：任务列表确认后一口气走完，只在真正阻塞时停（解决"AI 老停下要督促"）。
- **并行隔离审核 agent**：终审用独立干净上下文的子 agent 并发跑各视角，**避开"作者自审"的偏见**，主 agent 聚合修复。
- **抗压缩、可断点续做**：`tasks.md` + `openspec/` 落盘即真相源，会话中断后从第一个非 ✅ 任务接着走。

---

## 目录结构

```
dev-spec-flow/
├── SKILL.md                  ← Claude Code 入口（带 frontmatter，并行审核走原生子 agent）
├── AGENTS.md                 ← Codex 入口（内容一致，审核走顺序降级）
├── README.md                 ← 你正在看
├── references/               ← 各阶段细则（按需查阅）
│   ├── openspec-model.md      ← specs/changes/归档 + Requirement/Scenario + 分级【地基】
│   ├── research.md
│   ├── dev-rules.md
│   ├── code-review.md
│   ├── verification.md        ← 运行时验证 + 测试即任务
│   ├── git-flow.md
│   ├── review-agents.md       ← 并行隔离审核 agent 机制
│   ├── final-review.md        ← 终审 playbook
│   └── ui-design.md
└── templates/                ← 可复制的文档模板
    ├── proposal.md
    ├── spec.md                ← delta 规格
    ├── design.md
    ├── tasks.md
    └── review-report.md
```

> 工作流在**用户项目**里产出的文档放在该项目的 `openspec/` 下，与本 skill 目录无关。

---

## 安装

### Claude Code（推荐，能力最全）

把整个目录放到 skills 目录：

```bash
# 用户级（所有项目可用）
mv dev-spec-flow ~/.claude/skills/
# 或项目级
mv dev-spec-flow <你的项目>/.claude/skills/
```

最终路径应是 `.../skills/dev-spec-flow/SKILL.md`。

**验证**：打开 Claude Code，输入需求（如"帮我做个 X"），skill 应自动触发并进入 Phase 0 给出体量评估。也可手动 `/dev-spec-flow`。

> Claude Code 上 Phase 4 走**原生并行子 agent** + 内置 `/code-review` `/security-review` `/verify` 等，能力最全。

### Codex

Codex 通过项目根 `AGENTS.md` 自动加载。两种方式：

**方式一：直接复制到项目根**

```bash
cp dev-spec-flow/AGENTS.md <你的项目>/AGENTS.md
cp -r dev-spec-flow/references <你的项目>/.dev-spec-flow/references
cp -r dev-spec-flow/templates  <你的项目>/.dev-spec-flow/templates
```

然后把 `AGENTS.md` 里对 `references/...` / `templates/...` 的引用前缀改成 `.dev-spec-flow/references/...` / `.dev-spec-flow/templates/...`。

**方式二：项目已有 AGENTS.md，往里追加一段**

```markdown
## 开发工作流：dev-spec-flow
当用户描述新功能 / 系统 / 模块需求时，遵循 `.dev-spec-flow/AGENTS.md` 定义的 6 阶段工作流。
```

并把整个目录放到 `.dev-spec-flow/`：`cp -r dev-spec-flow <你的项目>/.dev-spec-flow`。

> Codex 没有并行子 agent / 内置 review skill，Phase 4 走**顺序降级**（每视角理想情况开新会话减小上下文污染），见 `references/review-agents.md` 末尾。

---

## 用户工作流示例

**1. 你给一个需求**

```
我想做一个支持团队协作的待办应用，类似 Linear 但更简单。要有项目分组、看板视图、@提醒。
```

**2. Phase 0：定级立项**

```
我判这是【Full / 超大】级（约 25 个任务，涉及 实时同步/鉴权/UI 多域）。
已建 openspec/changes/add-team-todo/。按规范走 2-3 道闸 + 2-3 波并行审核，确认吗？
```

**3. Phase 1：调研** → 拉技术栈/协作架构/看板 UI 参考，给技术决策摘要。

**4. Phase 2：写文档** → 在 `openspec/changes/add-team-todo/` 下生成 `proposal.md`、`specs/*/spec.md`（Requirement/Scenario）、`design.md`、`tasks.md`（25 任务分 5 里程碑、依赖图、每任务标注实现哪条 Requirement）。

**5. Phase 3：开发循环** → 建分支，按任务一个接一个做（改状态→实现→自检→测试→备注→✅→commit），里程碑边界跑验证 + push，**不停**。

**6. Phase 4：并行审核** → 并发派出功能/类型/性能/安全/UX 等视角的隔离子 agent，聚合 findings、逐条修复、写报告。

**7. Phase 5：归档** → delta merge 回 `openspec/specs/`，change 移入 archive，汇报总结。

---

## 自定义

- **触发关键词**：编辑 `SKILL.md` frontmatter 的 `description`。
- **分级阈值 / 审批闸**：改 `SKILL.md`、`AGENTS.md` 的分级表与 `references/openspec-model.md` 第六节。
- **审核视角 / 波数**：改 `references/review-agents.md` 的视角清单库与 `references/final-review.md` 的缩放表。
- **注释语言**：默认随项目主语言、无偏好默认中文，改 `references/dev-rules.md` 第 4 条。
- **依赖锁版策略**：改 `references/dev-rules.md` 第 3 条。

---

## 设计哲学

需求来自人类、常常模糊；把它变成**活的规格 + 一次改动的完整上下文**，按体量选最轻够用的严格度，按任务一口气走到底，每步留痕（commit、备注、审核报告），用与上下文隔离的并行 agent 把缺漏审出来，最后归档回真相源。

不追银弹，追**少返工、少遗漏、少中途停顿**。
