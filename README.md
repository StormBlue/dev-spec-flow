# dev-spec-flow

一个面向全栈工程的**规范驱动开发工作流** skill，把粗犷的需求描述变成扎实的需求文档 + 任务列表 + 多轮审核的工程实践。同时适配 **Claude Code** 和 **Codex**。

> 工作流摘要（详见 [`SKILL.md`](./SKILL.md) / [`AGENTS.md`](./AGENTS.md)）：
>
> ```
> Phase 0  体量评估 → 让用户确认走 1/5/10+ 轮审核
> Phase 1  调研     → context7 / WebSearch / 已有 skill / 阅读代码
> Phase 2  写文档   → docs/<feature>/requirements.md + tasks.md
> Phase 3  开发循环 → 每任务: 开发 → 自检 → 写备注 → commit/push → 下一个
> Phase 4  最终审核 → 小 1 / 中 5 / 超大 10+ 轮
> ```

---

## 目录结构

```
dev-spec-flow/
├── SKILL.md                  ← Claude Code skill 入口（带 frontmatter）
├── AGENTS.md                 ← Codex 入口（自动加载，无 frontmatter）
├── README.md                 ← 你正在看
├── references/               ← 各阶段细则（按需查阅）
│   ├── dev-rules.md
│   ├── code-review.md
│   ├── git-flow.md
│   ├── final-review.md
│   ├── research.md
│   └── ui-design.md
└── templates/                ← 可复制的文档模板
    ├── requirements.md
    ├── tasks.md
    └── review-report.md
```

---

## 安装

### Claude Code

把整个目录放到 Claude Code 的 skills 目录里。两种范围：

**用户级（推荐，所有项目可用）**：

```bash
# macOS / Linux
mv dev-spec-flow ~/.claude/skills/

# Windows (PowerShell)
Move-Item dev-spec-flow $HOME\.claude\skills\
```

最终路径应是 `~/.claude/skills/dev-spec-flow/SKILL.md`。

**项目级（只在某个项目里启用）**：

```bash
mv dev-spec-flow <你的项目>/.claude/skills/
```

最终路径应是 `<项目>/.claude/skills/dev-spec-flow/SKILL.md`。

**验证**：

打开 Claude Code，输入需求描述（如 "帮我做个 X"），skill 应自动触发，让 Claude 进入 Phase 0 给出体量评估。

也可以手动调用：

```
/dev-spec-flow
```

### Codex

Codex 通过项目根的 `AGENTS.md` 自动加载指令。两种集成方式：

**方式一：直接复制到项目根**

```bash
# 拷贝 AGENTS.md 到项目根（如果项目已有 AGENTS.md，看下方"已有 AGENTS.md"）
cp dev-spec-flow/AGENTS.md <你的项目>/AGENTS.md

# 把 references 和 templates 也带上（AGENTS.md 里会引用）
cp -r dev-spec-flow/references <你的项目>/.dev-spec-flow/references
cp -r dev-spec-flow/templates  <你的项目>/.dev-spec-flow/templates
```

然后在 `AGENTS.md` 里把对 `references/...` / `templates/...` 的引用前缀改成 `.dev-spec-flow/references/...` / `.dev-spec-flow/templates/...`。

**方式二：项目已有 AGENTS.md，往里追加**

在项目已有的 `AGENTS.md` 里加一段：

```markdown
## 开发工作流：dev-spec-flow

当用户描述新功能 / 系统 / 模块需求时，遵循 `.dev-spec-flow/AGENTS.md` 中定义的 4 阶段工作流：
体量评估 → 调研 → 文档 → 开发循环 → 多轮审核。详见该文件。
```

然后把 `dev-spec-flow/` 整个目录放到项目根的 `.dev-spec-flow/` 下：

```bash
cp -r dev-spec-flow <你的项目>/.dev-spec-flow
```

---

## 用户工作流示例

### 1. 你给一个需求

```
我想做一个支持团队协作的待办应用，类似 Linear 但更简单。
要有项目分组、看板视图、@提醒。
```

### 2. AI 进入 Phase 0：体量评估

```
我估这是【超大】量级：
- 任务约 25 个
- 工时约 5-7 工作日
- 影响约 40 个文件
- 涉及实时同步、鉴权、UI 等多领域

按规范应跑 10+ 轮最终审核。确认走这个量级吗？
```

### 3. 你确认后，AI 进入 Phase 1：调研

AI 用 context7 / WebSearch / 已有 skill 调研技术栈、协作架构、看板 UI 参考，给出技术决策摘要。

### 4. 你确认决策后，AI 进入 Phase 2：写文档

在 `docs/team-todo/` 下生成 `requirements.md` 和 `tasks.md`，带：

- 详尽功能 + 非功能需求
- 25 个任务分 5 个里程碑
- mermaid 依赖图
- 每个任务有备注块占位

### 5. 你确认文档后，AI 进入 Phase 3：开发循环

按任务列表一个接一个做：

- 改状态 ⏳ → 🚧
- 实现 + 自检
- 填备注块
- 改状态 ✅
- commit + push
- **不停**，立刻进入下一个

直到所有任务 ✅。

### 6. AI 进入 Phase 4：多轮审核

按 10+ 轮跑（功能 / 类型 / 性能 / 安全 / a11y / 跨模块 / 回归 / i18n / 文档 / 性能压测 / ...），每轮单独 commit + push。

最后给你完整总结。

---

## 自定义

### 修改触发关键词

Claude Code 通过 `SKILL.md` 的 `description` 字段决定何时触发 skill。如果你想加更多触发短语，编辑 frontmatter 里的 `description`。

### 修改量级阈值

默认 `≤5 / 5-20 / >20` 对应 `小 / 中 / 超大`。改 `SKILL.md` 和 `AGENTS.md` 里 Phase 0 的表格。

### 修改审核轮数

默认 `1 / 5 / 10+`。改同上 + `references/final-review.md`。

### 修改注释语言策略

默认随项目主语言走，无项目偏好时默认中文。改 `references/dev-rules.md` 第 4 条。

---

## 设计哲学

需求来自人类，常常是模糊的；让 AI 把模糊变成扎实的需求文档 + 可执行的任务列表，然后按列表一口气走到底，每步留下足够的痕迹（commit、备注、审核报告），最后用与体量匹配的多轮回顾把缺漏补完。

不追求银弹，追求**少返工、少遗漏、少中途停顿**。
