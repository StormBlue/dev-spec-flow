# Evidence 与验证策略

验证的目标是为验收主张取得足够可信、可复查的证据。Scenario 是验收示例，不天然要求新增一条自动化测试。

## 单一证据清单

一个 change 默认只维护 `verification.md`。每条记录至少包含：

```yaml
id: AC-1
status: passed
validates:
  - REQ-2026-042#AC-1
  - SC-auth-012
methods:
  - command
evidence:
  - kind: command
    ref: openspec/changes/add-session-expiry/evidence/auth-check.txt
    description: "Captured command and observed 401 result without a token"
```

执行时间和整体 revision 分别记录在 verification metadata 的 `verified_at` 与
`verified_against`；后者优先使用覆盖本次实现的完整不可变 Git commit OID。若验证发生在 commit
前，把 base commit、排序后的 in-scope 路径、逐文件 hash、删除项与工作树状态写入 change 下的
deterministic revision capture，再使用 `sha256:<capture-digest>@<repository-relative-capture>`。
单文件 hash 只有在变更确实只涉及该文件时才能代表整体 revision。不要使用 `HEAD`、分支或 tag。
单条 evidence 保持 docs-architect 的 `kind/ref/description` 形状。

`AC-N` 是 proposal 内的局部序列化 ID；verification 的 `id` 可以保持 `AC-N` 以与 proposal
一一匹配。`validates` 在同一 change 内可使用该局部形式，但需要跨 artifact/change 消歧时使用
`<REQ-ID>#AC-N`。BR/SC 始终使用其全局稳定 ID。

`ref` 必须可检查：仓库相对路径及 locator、不可变 commit/PR、耐久 URL、捕获结果或截图。计划运行的命令、测试源码存在或一句“已验证”都不是执行成功的证据。

Close readiness 对 `passed` acceptance、passed review 和 aggregate command/log 另有一层
observed capture 门禁：至少一条 evidence 必须是 `command`、`log`、`screenshot` 或
`document`，且指向当前 change 下的普通文件（通常是 `evidence/`），不能带测试 locator。
测试源码、任意生产文件和 commit 只能作为 supporting reference，不能单独声称命令已经执行。
`evidence/` 不是另一份 manifest：只放实际观察 capture，并由 `verification.md` 统一解释。仍被
验收、review、revision anchor 或 completion summary 引用的 capture 必须保留；只有解除所有引用
并显式登记到 `ephemeral_artifacts` 后，summary/minimal close 才可删除。

## 可选证据方法

| Method | 适用情况 | 最低记录 |
|---|---|---|
| `existing-test` | 已有测试准确覆盖本次行为且仍适用 | 测试 locator + 本次实际运行结果 |
| `automated` | 稳定且有持续回归价值的行为 | 新/改测试 locator + 实际结果 |
| `command` | build、lint、typecheck、migration check、benchmark | 完整命令、环境要点、退出/测量结果 |
| `runtime` | 服务、CLI、桌面/移动应用真实运行 | 启动方式、输入、观察结果 |
| `inspection` | 配置、生成物、静态约束或小型文案检查 | 检查范围、判据、观察结果 |
| `screenshot` | UI 布局、视觉状态、跨视口 | 图片路径、viewport/state、关联 AC/SC |

`not_applicable` 是 acceptance 结果而不是 evidence method；通过带 authority、reason 和
证据的 `waived` verification 结果表达。

可以用一种证据覆盖多个 AC/SC，也可为一个高风险 AC 组合多种证据。关系必须显式。

## 何时新增自动化测试

以下情况通常值得新增或强化自动化测试：

- 修复过的缺陷需要可靠复现并防止回归；
- 公共 API、数据格式、协议或稳定业务规则；
- 鉴权、金额、权限、迁移、幂等、并发等高后果边界；
- 多个消费者依赖且人工验证容易遗漏；
- 测试可稳定、快速运行，维护成本低于其预防价值。

以下情况不默认新增永久测试：

- 文案、样式微调或一次性配置，inspection/screenshot 更直接；
- 已有较低层测试充分覆盖，新增测试只重复同一断言；
- 行为依赖脆弱的外部环境，稳定契约检查或受控 inspection/runtime 更可信；
- 为测试 trivial glue 需要大量 mock，且不能证明真实行为；
- 项目没有测试基建，而引入框架的成本/边界尚未获授权。

不要为覆盖率数字测试无意义实现细节，也不要因“不是自动化”而把可复查证据降格为无效。

## 验证时机与范围

### Apply 期间

在一个连贯实现单元结束时运行 **impacted checks**：与改动直接相关的现有测试、静态检查、构建或短 smoke。尽早验证高风险假设。不要每个机械子任务都重复全套命令。

### Verify / Close 前

仅补齐缺失、陈旧或因后续改动失效的证据：

1. 对照 AC/SC 清单找缺口。
2. 检查证据 revision 与当前 diff 是否仍匹配。
3. 按风险决定是否需要更广 regression、真实运行、迁移/回滚或专项测量。
4. 将实际结果写入 `verification.md`。

若 apply 期间的可信结果仍覆盖当前代码，不因进入 verify/review/close 再跑同一检查。review 负责判断证据是否充分，只有证据缺失、矛盾、陈旧或需要复现 finding 时才重跑。

Close 只改变生命周期字段、引用路径、压缩内容或 archive 位置时，不会自动使行为证据失效；CLI
应重写受影响的 repository-relative refs。若 Close 同时修改实现、当前行为条款或被验证的 durable
文档内容，则必须重新运行受影响检查并更新 `verified_at`/`verified_against`。

当目标仓库启用 docs-architect 时，`documentation_checks` 必须分别记录成功的
`operation: impact`、`operation: check` 和 `operation: index` 捕获。三者都应引用 change
下的 JSON 结果；`impact` 至少含 changed/affected/findings 数组，`check` 的 summary.errors
必须为 0，`index` 必须证明 `write: true`。一条普通 command 描述不能复用为三种握手。

## 失败、延期与豁免

- 失败证据必须保留到问题解决，并记录后续通过证据；不得覆盖失败历史来伪装一次通过。
- `deferred` 不能直接满足原验收条件。要么保持 requirement 未完成，要么把剩余范围转成有稳定 ID 的新 requirement/issue，并取得对原 acceptance 变更的授权。
- waiver 表示经可解析的人类授权确认该验收不适用，Close 时映射为 `not_applicable`；它必须同时有 authority、理由和证明该处置的 evidence，不能表示“未验证但算通过”，也不能由实现 agent 自批。
- 需要真实第三方、密钥或设备而无法验证时，明确缺口和影响；风险不允许时不得 close。

## Close readiness

`close` 前逐项确认：

- 所有 AC 状态为 `passed` 或有证据的 `not_applicable`；
- 每项至少一个可解析证据，且证据支持其主张；
- 高风险 driver 的负路径、回滚或契约保障已覆盖；
- 项目要求的 build/lint/typecheck/test 门禁已实际运行，或有明确不适用理由；
- 文档影响已处理，见 [docs-architect-integration.md](docs-architect-integration.md)；
- 未解决问题没有被埋在自由文本里。
