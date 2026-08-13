# 动作式工作流

本工作流由可组合动作组成，不是必须逐级通过的固定阶段。每次只选择当前目标所需的动作；artifact 之间的依赖负责说明“现在可以做什么”，不把流程变成仪式。

```text
intake -> explore? -> propose/update -> apply -> verify? -> close
                  \____________________^      \_____/
```

`?` 表示按未知程度、改动内容与失败风险触发。实现中发现规格或设计不成立时，回到 `propose/update` 修正，再继续 `apply`。

## 共同前置检查

执行任何动作前：

1. 读取仓库内适用的 `AGENTS.md`、`CLAUDE.md`、Cursor rules、贡献指南与项目配置。
2. 检查 Git 状态，保护用户已有改动；确认当前分支与用户要求。
3. 读取相关源码、`openspec/specs/` 和仍在进行的 change，避免重复立项或违反现有行为。
4. 检测当前环境实际提供的工具、skills、子 agent、浏览器和验证能力，见 [platforms.md](platforms.md)。
5. 按 [risk-policy.md](risk-policy.md) 分别判断协作复杂度与失败风险；二者不能互相替代。
6. 若仓库启用了 docs-architect，按 [docs-architect-integration.md](docs-architect-integration.md) 复用其 ID、关系、生命周期和检查，不创建第二套真相源。

## 选择动作

| 动作 | 何时选择 | 主要结果 |
|---|---|---|
| `intake` | 新需求尚未形成稳定记录，或需确认是否已有相同意图 | 创建或定位一个稳定的 requirement/change |
| `explore` | 技术、产品、代码现状或风险存在会改变方案的未知 | 有来源的结论、风险与开放问题；原始笔记默认临时 |
| `propose/update` | 需要明确意图、行为增量、设计或执行路径；实现发现事实变化时也用 | 更新 proposal、delta spec、按需 design 与 tasks |
| `apply` | 当前有一个依赖已满足、边界足够明确的 ready task | 实现一个连贯改动并留下必要进度与证据 |
| `verify` | 需要取得验收证据，或风险要求独立/更强验证 | 更新单一 `verification.md`；不重复已有可信证据 |
| `close` | change 意图已经达成，需要同步长期真相并及时清理归档 | 原子化合并、文档同步、压缩、归档与校验 |

动作不是用户必须记住的命令。根据用户意图和仓库状态自动选择；只有真正需要外部决定时才暂停。

## Artifact 依赖

```text
proposal(requirement) -----> delta spec ---------+
          |                      |                |
          +-----> design? -------+-----> tasks ---+-----> apply
                                                        |
                              verification <------------+
                                      |
                                      +-----> close
```

- `proposal.md` 拥有动机、范围、验收条件和生命周期。
- delta spec 拥有将要改变的可观察行为。
- `design.md` 只在决策复杂度值得记录时创建。
- `tasks.md` 拥有依赖、执行进度、恢复点与结果，不拥有需求本身。
- `verification.md` 是唯一证据清单，测试、命令、检查、截图等都在这里引用。
- `openspec/specs/` 只描述已交付的当前行为，在 `close` 时更新。

详细边界与 ID 见 [openspec-model.md](openspec-model.md)。

## 各动作契约

### `intake`

1. 在 active change、archive、主 specs 和索引中搜索重复意图。
2. 重复需求更新原记录；相关但独立的意图用关系连接，不复用 ID。
3. 分配稳定 `REQ-YYYY-NNN` 和可读 slug，记录真实 `created_at`、origin、开放问题。
4. 判断用户当前指令是否明确授权了将要执行的范围。明确的命令式请求本身可以作为批准，无需再问一次；仅要求分析、调研、提案或评审，不授权实现、commit、push、deploy 或破坏性操作。
5. 若批准只存在于当前会话且没有可解析的 issue/commit/document，创建 `request.md`，忠实记录来源、明确授权范围与时间，并让 proposal `approval` 指向该 request record。不要由 agent 扩写权限或自我批准。
6. 未获得可解析的用户或仓库授权时，不把需求标为 `accepted` 或后续状态。

### `explore`

先研究项目自身，再查询当前官方资料或外部实践。只研究会影响决策的未知；达到停止条件后把结论写回 proposal/design/risk，删除或不落原始探索噪声。详见 [research.md](research.md)。

### `propose/update`

按需要创建最小 artifact 集：

- 可观察行为改变时必须有 delta spec。
- 有多步执行或需跨会话恢复时创建 tasks。
- 跨边界、新依赖、迁移、安全、回滚困难或重要权衡时创建 design。
- 纯内部且简单的改动不为填模板制造空 artifact。

每个验收条件与行为条款使用稳定 ID；tasks 通过 ID 引用它们。文档就绪的含义是关键边界明确、无阻止当前 ready task 的开放问题，不要求所有未来细节一次写死。

### `apply`

1. 优先恢复已有 `in_progress` task；否则从依赖已满足的任务中选择最高优先级者。
2. 将任务标为 `in_progress`，实现一个可评审的连贯单元。
3. 运行与当前影响面匹配的检查，记录实际结果；是否新增测试由 [verification.md](verification.md) 决定。
4. 自检 diff，见 [code-review.md](code-review.md)。
5. 更新因实现事实而改变的 proposal/spec/design/tasks，只记录有复用价值的发现与恢复信息。
6. 验收证据充分后标为完成，并按用户授权与项目 Git 约定形成提交；不要求每个机械子任务独占一个 commit，也不把开发请求自动扩大为 commit/push 权限。
7. 立即选择下一个 ready task，直到意图完成或遇到真实阻塞。

### `verify`

对仍缺证据的 AC/Scenario 选择最低成本、足够可信的方法。复用仍然适用的现有证据，不因进入新动作而重跑相同命令。风险升高、证据陈旧/矛盾或改动扩大时提高验证强度。详见 [verification.md](verification.md)。

### `close`

`close` 是完成定义的一部分，不是可遗忘的善后。它合并 delta、同步长期文档、解决或转移 findings、压缩临时材料、写入完成/归档时间、移动 archive，并运行结构检查。任一步失败都不声称完成；按 [close-and-retention.md](close-and-retention.md) 从断点幂等恢复。

## 何时暂停

只在下列情况暂停并提出一个具体问题：

- 不同答案会实质改变范围或外部行为，且仓库中无法推断；
- 需要用户选择供应商、成本、密钥、合规或产品策略；
- 需要未授权的破坏性操作或外部发布；
- 同一失败经过有依据的多次修复仍无法推进；
- 外部系统不可用且没有本地替代证据。

普通实现细节、可逆的项目内选择和已确认任务之间的切换不构成暂停理由。
