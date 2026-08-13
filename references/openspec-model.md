# OpenSpec 文档与生命周期模型

本模型把“当前真相”与“一次改动”分开，同时用稳定 ID、真实时间和证据关系连接需求、行为、任务与验证。

## 目录与所有权

```text
openspec/
├── specs/                              # 已交付行为的唯一真相源
│   └── <domain>/spec.md                # product-spec: SPEC-<domain>
└── changes/
    ├── <slug>/                         # active change
    │   ├── request.md                  # 按需保存可解析的用户授权
    │   ├── proposal.md                 # requirement: REQ-YYYY-NNN
    │   ├── specs/<domain>/spec.md      # 临时 delta，不是第二份 product-spec
    │   ├── design.md                   # 按需，change-local
    │   ├── tasks.md                    # exec-plan
    │   ├── verification.md             # 单一 evidence manifest
    │   └── evidence/                    # 按需保存实际观察的输出/截图/记录
    └── archive/
        └── <YYYY-MM-DD>-<REQ-ID>-<slug>/
```

| Artifact | 拥有 | 不应拥有 |
|---|---|---|
| `request.md` | 当前会话中明确授权的忠实、可解析记录（仅在没有其它 durable authority 时） | agent 推断、扩大后的权限或实现事实 |
| `proposal.md` | 动机、范围、验收、origin/approval、风险、生命周期 | 行为条款全文、实现日志 |
| 主 `spec.md` | 当前可观察行为、边界与例外 | 未来计划、审批、任务状态 |
| delta spec | 本 change 对主 spec 的增删改 | 独立生命周期或重复 product-spec metadata |
| `design.md` | change 内技术选择、权衡、迁移/回滚 | 长期跨 change 决策的唯一副本 |
| `tasks.md` | 顺序、依赖、进度、恢复点、material discovery | 需求批准与当前系统真相 |
| `verification.md` | 实际证据、结果、waiver、综合 review 结论 | 没有可检查引用的重复主张 |
| `evidence/` | 被 `verification.md` 引用的原始观察 capture | 第二份 evidence 清单、未引用的 session 噪声 |

跨 change 仍有价值的重要技术决策提升为 ADR；当前架构和操作方式同步到 `docs/` 或 `ARCHITECTURE.md`。与 docs-architect 的完整映射见 [docs-architect-integration.md](docs-architect-integration.md)。

## 稳定 ID

身份不能依赖标题、目录名或 Markdown 顺序：

| 对象 | 格式 | 示例 |
|---|---|---|
| Requirement/change intent | `REQ-YYYY-NNN` | `REQ-2026-042` |
| 主 product spec | `SPEC-<domain>` | `SPEC-auth` |
| 行为条款 | `BR-<domain>-NNN` | `BR-auth-007` |
| Scenario | `SC-<domain>-NNN` | `SC-auth-012` |
| Acceptance criterion | `<REQ-ID>#AC-N` | `REQ-2026-042#AC-2` |
| Task | change 内 `T-NNN` | `T-003` |

- 分配前搜索 active、archive、主 specs 与生成索引；已使用的 ID 永不回收。
- 标题、slug、路径变化不改变 ID。
- `AC-N` 只在其 REQ 内唯一；完整身份是 `<REQ-ID>#AC-N`。proposal metadata 以及同一 change 的 tasks/verification 可以用局部 `AC-N`，因为父 REQ 已明确；跨 change、issue、ADR 或外部索引引用时使用完整身份。批准后不静默改写内容，授权变更写进 history。
- task 使用 `implements` 引用 AC/BR；evidence 使用 `validates` 多对多引用 AC/BR/SC。一个 evidence item 可以覆盖多个 Scenario，不要求为每条 Scenario 新建测试。
- 主 spec 与 delta 中把 ID 写在条款/场景标题或紧邻的机器可读字段中，确保 merge 不依赖可变标题。

## 时间与生命周期

目录日期和文件 mtime 不是生命周期真相。proposal 的机器可读 metadata 至少记录：

```yaml
id: REQ-2026-042
slug: add-team-todo
status: in_progress
created_at: 2026-08-13T09:10:00+08:00
updated_at: 2026-08-13T11:25:00+08:00
status_changed_at: 2026-08-13T10:00:00+08:00
completed_at: null
archived_at: null
status_history:
  - from: planned
    to: in_progress
    at: 2026-08-13T10:00:00+08:00
    evidence: request-record-or-commit
```

- 时间使用带时区的 ISO 8601；只记录真实发生的事件。
- `created_at` 永不改变；内容实质更新时更新 `updated_at`。
- 状态变化追加 `status_history`，不覆写历史；`status_changed_at` 等于最后一个事件时间。
- 采用 docs-architect 时，requirement 状态使用其生命周期：`intake -> clarifying -> accepted -> planned -> in_progress -> verifying -> documented -> done`，以及 `deferred/rejected/superseded`。
- `completed_at` 仅在验收、文档和验证 gate 都满足时写入；`archived_at` 仅在文件实际进入 archive 时写入。
- 索引按这些字段排序并分 active/history；不要按路径、标题或文件时间猜顺序。

## Proposal 与验收

proposal 保持精炼，包含：

- Why、期望结果、origin 与独立 approval；
- In scope / Out of scope；
- New/Modified capabilities；
- 稳定的 Acceptance Criteria（`AC-N`）；
- 协作复杂度与风险 driver；
- 影响面、依赖、开放问题、documentation disposition；
- 生命周期 metadata 与 history。

验收条件描述可观察结果，不预设一定用自动化测试证明。证据方法由 [verification.md](verification.md) 选择。

明确的命令式用户请求可以批准它明示的执行范围，不要求形式化的第二轮批准。若该批准只存在于会话中，使用 change-local `request.md` 固化为 `request-record`；若已有可解析 commit、document、issue 或 PR authority，直接引用它而不重复创建 request。分析/调研请求只构成 origin，不批准实现或 Git/发布动作。

## Requirement 与 Scenario

spec 描述系统“做什么”，不描述类名、依赖库或实现步骤。

```markdown
### Requirement: BR-auth-007 会话闲置过期
系统 SHALL 在认证会话连续 15 分钟无活动后使其失效。

#### Scenario: SC-auth-012 闲置达到上限
- **WHEN** 认证会话连续 15 分钟无活动
- **THEN** 后续受保护请求返回未认证结果
```

- `### Requirement:` 使用 SHALL/MUST/SHOULD/MAY 表达约束。
- 每条行为至少一个 `#### Scenario:`，恰好四个 `#`。
- Scenario 是验收示例与证据锚点，不等同于一条永久自动化测试。
- 性能、安全、可访问性等只有在确属产品/运营契约且可观察时才进入 spec；实现策略放 design。

## Delta 操作

change spec 只写增量：

- `ADDED`：新 ID，关闭时追加到主 spec。
- `MODIFIED`：引用已有 BR ID，并给出该条款的完整新内容；按 ID 替换。
- `REMOVED`：引用已有 BR ID，必须记录 reason、迁移/兼容影响；关闭时删除。
- `RENAMED`：引用同一 BR ID，只改标题；身份不变。

Scenario 的增删改同样按 SC ID。若两个 active change 修改同一 BR/SC，`close` 前必须显式解决冲突；不能以“最后写入者获胜”覆盖。

## Task 模型与恢复

task 至少包含稳定 ID、status、priority、`depends_on`、`implements`、验收/证据计划和必要恢复信息。

状态可使用 `pending`、`ready`、`in_progress`、`blocked`、`completed`、`cancelled`。emoji 只可作为显示，不是机器真相。`cancelled` 必须在 plan metadata 的 `cancellations` 中记录 task ID、具体原因和可解析授权；没有处置记录不能 close。

续做顺序：

1. 恢复唯一的 `in_progress` task；检查 Git diff 和 recovery note。
2. 没有进行中任务时，计算依赖全部 `completed` 的 ready 集合。
3. 从 ready 集合选最高优先级；同优先级按稳定 task ID。
4. `blocked` task 记录外部条件，不阻塞无依赖关系的 ready task。

不要使用“第一个非完成任务”，它会违反依赖与优先级。

## 追溯闭环

闭环要求“有关系且有证据”，不要求一对一测试：

```text
REQ#AC / BR / SC --implements--> Task --produces--> change
REQ#AC / SC       <--validates--- Evidence
change            --documents---> current spec/system docs
```

关闭前确认：

- 每个 AC 有可解析证据或经授权的 not-applicable 处置；
- 每个新增/修改 BR 至少被一个 task 覆盖；
- 每个 SC 有一种足够的验证方式和实际结果；
- 每个完成 task 的实现/证据引用可定位；
- 所有未解决 finding 已修复、拒绝并说明，或转成稳定的 REQ/issue/ADR/waiver。

## Close 与归档

归档不是“原样搬走全部文件”。它是知识压缩：delta 合并到主 spec，长期知识提升到 system docs/ADR，只保留能解释意图与证明完成的 change 记录，清除已解决的临时噪声。完整事务、保留 profile 与恢复规则见 [close-and-retention.md](close-and-retention.md)。
