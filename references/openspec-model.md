# OpenSpec 模型：specs（真相源）+ changes（增量提案）+ 归档

这是本 skill 文档体系的地基，融合自 [OpenSpec](https://github.com/Fission-AI/OpenSpec) 的核心思想。Phase 2 写文档、Phase 5 归档都建立在这套模型上。

---

## 一、心智模型

把项目的「规格」拆成两块，互不污染：

```
┌────────────────────────────────────────────────────────────────┐
│                          openspec/                               │
│                                                                  │
│   ┌────────────────────┐        ┌────────────────────────────┐  │
│   │      specs/         │        │         changes/           │  │
│   │                     │◄───────│  每个需求 = 一个文件夹      │  │
│   │  真相源             │ 归档时  │  proposal + delta spec     │  │
│   │  系统【当前】怎么工作│ merge   │  + design(可选) + tasks    │  │
│   │  （已交付的行为）    │        │  （【将要】怎么改）         │  │
│   └────────────────────┘        └────────────────────────────┘  │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

- **`specs/`** = 真相源，描述系统**此刻**的行为契约。只有归档时才更新。
- **`changes/<id>/`** = 一次改动的全部上下文（为什么改、改成什么、怎么实现、做哪些任务）。开发期都在这里。
- **归档** = 改动做完后，把 change 里的 delta 合并进 `specs/`，再把整个 change 文件夹挪进 `changes/archive/`。`specs/` 于是长成了系统的活文档。

**为什么这么分**：
- **brownfield 友好**：大多数开发是改已有系统，不是从零建。delta（只写"改了什么"）天然适合。
- **可并行**：多个 change 同时进行互不冲突（只要不改同一条 requirement）。
- **审查友好**：review 一个 change 文件夹，所有上下文都在一处。
- **可追溯**：archive 永久保留"为什么这么改"，半年后回看不抓瞎。

> 本 skill 用**手工维护**这套目录即可，不依赖 OpenSpec CLI。若项目已装 `@fission-ai/openspec`，目录约定完全兼容，可直接用其 `openspec` 命令。

---

## 二、目录布局

```
openspec/
├── specs/                      ← 真相源，按 domain 分组
│   ├── auth/spec.md
│   ├── payments/spec.md
│   └── ...
└── changes/
    ├── add-2fa/                ← 进行中的 change
    │   ├── proposal.md         ← 为什么 + 改什么（必有）
    │   ├── design.md           ← 怎么实现（仅复杂时）
    │   ├── tasks.md            ← 任务清单（必有，指挥棒）
    │   └── specs/              ← delta：本次对 specs/ 的增删改
    │       └── auth/spec.md
    └── archive/
        └── 2026-06-01-add-sso/ ← 已完成，已 merge 回 specs/
            └── ...
```

**domain 分组**：按 feature 域（`auth/`、`payments/`）、组件（`api/`、`frontend/`）或限界上下文（`ordering/`、`fulfillment/`）划分，选对项目最自然的一种。

**greenfield（全新项目）**：第一个 change 的 delta 几乎全是 `## ADDED`；归档后 `specs/` 被"种"出来，后续 change 就有真相源可对照了。

**change-id 命名**：kebab-case，动词起头，描述意图——`add-dark-mode`、`fix-login-race`、`refactor-payment-flow`。

---

## 三、change 文件夹里的 artifact

artifact 之间是**「使能」而非「闸门」**关系（fluid not rigid）：依赖图告诉你"现在可以写哪个"，不是"必须先写完哪个"。实现中发现 design 错了，回头改 design 再继续——这是常态，不是例外。

```
proposal ──────► spec(delta) ──────► design ──────► tasks ──────► 实现
   why              what(契约)        how(可选)      steps
 + 范围 + 能力
```

### 1. `proposal.md` — 为什么 + 改什么

模板：[`templates/proposal.md`](../templates/proposal.md)。保持精炼（1-2 页），聚焦 **why**，实现细节留给 design。必含：

- **Why**：要解决的问题 / 机会，1-2 句。为什么是现在。
- **What Changes**：要做的改动清单，破坏性改动标 **BREAKING**。
- **Capabilities**：本次涉及哪些 spec——
  - *New Capabilities*：要新建的能力，每个对应一个 `specs/<name>/spec.md`（kebab-case）。
  - *Modified Capabilities*：要改 requirement 的已有能力（仅当 spec 级行为变化，不是实现细节）。先查 `openspec/specs/` 里已有的名字。
- **范围**：in scope / out of scope（写出不做的，避免误解）。
- **成功标准**：怎么算做完了（可度量）。
- **Impact**：影响的代码 / API / 依赖 / 系统。
- **开放问题**：留给用户拍板的（选型、第三方资源等）。

> Capabilities 是 proposal 与 spec 阶段之间的**契约**——这里列了几个能力，spec 阶段就要产出对应几个 spec 文件。

### 2. `specs/<domain>/spec.md` — 行为契约（delta）

模板：[`templates/spec.md`](../templates/spec.md)。这是 change 对真相源的**增量**。详见下面「四、写 spec」。

### 3. `design.md` — 怎么实现（**仅按需创建**）

模板：[`templates/design.md`](../templates/design.md)。**满足任一条才写**，否则跳过（这是给小任务松绑的关键）：

- 跨模块 / 多服务，或引入新架构模式
- 新外部依赖，或重大数据模型变化
- 安全 / 性能 / 迁移有复杂度
- 存在歧义，编码前先做技术决策更划算

含：Context、Goals/Non-Goals、Decisions（选 X 不选 Y 的理由 + 备选）、Risks/Trade-offs、Migration Plan、Open Questions。**技术栈与版本、架构图、数据模型、非功能需求落点**也放这里。

### 4. `tasks.md` — 任务清单（指挥棒）

模板：[`templates/tasks.md`](../templates/tasks.md)。开发期的核心。保留本 skill 的强化：分层（里程碑→任务→子任务）、依赖图、状态 emoji、备注块，并**每个任务标注它实现哪条 Requirement**（见「六、闭环」）。

---

## 四、写 spec：Requirement + Scenario

spec 是**行为契约**，不是实现计划。描述"系统做什么"（可观察行为、输入输出、错误条件、外部约束），不写"怎么做"（类名、库选型、步骤——那是 design/tasks 的事）。

**快速判据**：如果实现可以改而外部可观察行为不变，那它就不该进 spec。

### 格式

```markdown
## Purpose
本 spec 域的一句话描述。

## Requirements

### Requirement: 用户认证
系统 SHALL 在登录成功后签发 JWT token。

#### Scenario: 凭据有效
- **WHEN** 用户提交正确的邮箱 + 密码
- **THEN** 返回 JWT token
- **AND** 跳转到 dashboard

#### Scenario: 凭据无效
- **WHEN** 用户提交错误凭据
- **THEN** 展示错误信息
- **AND** 不签发 token
```

**硬规则**：

| 元素 | 规则 |
|------|------|
| `### Requirement:` | 一条具体行为。用 **SHALL / MUST**（强制）、SHOULD（推荐）、MAY（可选）——RFC 2119 关键词，避免模糊的"应该"。 |
| `#### Scenario:` | **必须正好 4 个井号 `####`**。每条 Requirement **至少一个** Scenario。 |
| WHEN / THEN / AND | scenario 用 Given/When/Then 结构。**每个 scenario 都是一个潜在测试用例**——这是需求与测试之间的桥（见 [`verification.md`](verification.md)）。 |

### 非功能需求也写成 Requirement

性能、安全、可访问性等都是可测的行为契约，照样用 Requirement + Scenario：

```markdown
### Requirement: 列表接口性能
系统 SHALL 在 1 万行数据下保持 p95 响应 < 300ms。

#### Scenario: 万行分页查询
- **WHEN** 表中有 10000 行，请求第一页（pageSize=50）
- **THEN** p95 响应时间 < 300ms
- **AND** 走索引，不全表扫描
```

---

## 五、delta：ADDED / MODIFIED / REMOVED

change 里的 `specs/` 写的是**增量**，不重述整份 spec。用 `##` 头分区：

```markdown
## ADDED Requirements
### Requirement: 双因子认证
系统 MUST 支持 TOTP 双因子认证。
#### Scenario: 启用 2FA
- **WHEN** 用户在设置里启用 2FA
- **THEN** 展示 QR 码供 authenticator app 绑定

## MODIFIED Requirements
### Requirement: 会话过期
系统 MUST 在 15 分钟无活动后过期会话。（原为 30 分钟）
#### Scenario: 闲置超时
- **WHEN** 认证会话 15 分钟无活动
- **THEN** 会话失效

## REMOVED Requirements
### Requirement: 记住我
**Reason**: 被 2FA 取代
**Migration**: 用户每次会话重新认证
```

| 分区 | 含义 | 归档时 |
|------|------|--------|
| `## ADDED Requirements` | 新增行为 | 追加进主 spec |
| `## MODIFIED Requirements` | 改变行为（**必须粘贴整条 requirement 的完整新内容**，不能只写片段，否则归档丢细节） | 替换主 spec 中同名 requirement |
| `## REMOVED Requirements` | 废弃行为（**必须写 Reason + Migration**） | 从主 spec 删除 |
| `## RENAMED Requirements` | 仅改名（FROM:/TO: 格式） | 改名 |

**MODIFIED 工作流**：① 在 `openspec/specs/<domain>/spec.md` 找到原 requirement → ② 整块复制（从 `### Requirement:` 到所有 scenario）→ ③ 粘到 `## MODIFIED` 下编辑 → ④ 头部文字与原文完全一致（空白不敏感）。若只是加新关注点而不改原行为，用 ADDED 而非 MODIFIED。

---

## 六、分级：Lite / Standard / Full（渐进严格度）

**用最轻、但仍能让改动可验证的那一级**。绝大多数改动停在 Lite。分级在 Phase 0 提出、调研后敲定。

| 级别（对应量级） | 何时 | 必写 artifact | design.md | spec 粒度 | 审核 |
|---|---|---|---|---|---|
| **Lite（小）** | 单模块、行为清晰、低风险 | proposal(精简) + tasks + 轻量 delta spec | 跳过 | 几条核心 requirement + 验收 | 1 轮综合（1-2 个并行 agent） |
| **Standard（中）** | 跨模块、有一定复杂度 | proposal + spec + tasks，design 视情况 | 按需 | 完整 requirement/scenario | 一波 4-5 视角并行 agent |
| **Full（超大）** | 多域 / 新系统 / 高风险（API 契约、迁移、安全） | 全套 artifact，可能多个 change | 必写 | 完整 + 边界场景齐全 | 2-3 波 8-12 视角并行 agent |

详见 [`final-review.md`](final-review.md) 的审核缩放、[SKILL.md](../SKILL.md) Phase 0 的闸门缩放。

---

## 七、需求↔任务↔审核 闭环（traceability）

防"做漏一条需求 / 审了个寂寞"。三个锚点扣起来：

1. **每条 Requirement → ≥1 个 task**。`tasks.md` 里每个任务标注 `实现：R-<domain>-<n>`（或直接引用 Requirement 名）。写完 tasks 后自查：有没有 Requirement 没有任何任务覆盖？
2. **每个 Scenario → 一个验证点**。Scenario 就是测试用例：开发期写成自动化测试（见 [`verification.md`](verification.md)），终审期逐条核对。
3. **终审按 Scenario 清单核对**：[`final-review.md`](final-review.md) 的功能视角 agent 必须拿着 spec 的 scenario 列表，逐条确认"真的能跑通"。

---

## 八、归档（Phase 5）

change 全部任务 ✅ 且审核通过后：

1. **merge delta**：把 change 的 `specs/` 里每个 ADDED/MODIFIED/REMOVED 应用到 `openspec/specs/<domain>/spec.md`（主 spec 里是干净的、非 delta 的 requirement 列表）。
2. **移到 archive**：`changes/<id>/` → `changes/archive/<YYYY-MM-DD>-<id>/`，全部 artifact 原样保留。
3. **校验**：merge 后通读主 spec，确认无重复/冲突 requirement。
4. commit（见 [`git-flow.md`](git-flow.md)）。

**良性循环**：specs 描述现状 → change 提增量 → 实现 → 归档 merge → specs 描述新现状 → 下个 change 在新 specs 上构建。

> 何时归档：一个 change 的**意图达成**即可归档。若范围爆炸成另一件事，开新 change 而非无限改旧的（"update 保留上下文，new change 提供清晰度"）。
