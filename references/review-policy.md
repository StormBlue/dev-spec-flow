# 风险驱动审核策略

审核的目标是用独立视角发现实现、规格和证据之间的偏差，不是生成固定数量的报告。

## 默认策略

每个 change 默认做一次综合 diff/spec review，覆盖：

- 实现是否满足 proposal 的 AC 与 delta spec 的 BR/SC；
- 错误路径、边界、回归和项目约定；
- `verification.md` 的证据是否真实、适用且覆盖当前 revision；
- 实现、design、主文档与 change 文档是否一致；
- 是否存在无关改动、秘密、生成物或遗漏的迁移/发布事项。

低风险、极小且已被现有门禁充分覆盖的 change，可以由实现者的独立 diff 自检承担综合 review；记录结论到 `verification.md`，不创建空报告。

## 何时增加专项视角

只有 [risk-policy.md](risk-policy.md) 中的 driver、实现发现或综合 review finding 需要时才追加：

| Trigger | 专项视角 |
|---|---|
| 鉴权、PII、输入执行、权限边界 | security/privacy |
| schema/data rewrite、回填、不可逆写入 | data migration/integrity |
| 公共 API、事件、SDK、多模块交互 | contract/integration |
| 热路径、容量目标、资源约束 | performance/scale |
| 新/显著 UI 流程 | UX/accessibility |
| 部署、启动、告警、外部依赖降级 | operations/observability |
| 并发、金额、权限授予 | domain-specific correctness |
| 影响面广或底层共享组件 | regression/blast radius |

不设 reviewer 个数、视角下限或固定波次。不相关视角不审；一个 reviewer 可以覆盖相关的多个视角。

## Review 与 Verify 的边界

- verify 产生行为证据；review 审查代码、契约和证据是否一致。
- reviewer 首先读取已有证据，不默认逐 Scenario 重跑。
- 只有证据不足、陈旧、矛盾或 finding 需要复现时才运行额外命令。
- 安全、迁移、性能等专项可以产生新的验证证据，统一写回 `verification.md`。

## Finding 规则

每个 actionable finding 包含 severity、位置、现象、影响、违反的 AC/BR/项目约束和建议方向：

- `P0`：安全漏洞、数据损坏、不可发布或核心意图完全失败。
- `P1`：用户可见错误、重要边界遗漏、显著回归或高概率运维失败。
- `P2`：有明确价值但不阻止当前意图的改进。

关闭前每个 finding 必须有一个明确 disposition：

- `fixed`：附修复与验证证据；
- `rejected`：说明为什么不成立，并附可检查依据；
- `transferred`：链接到稳定 REQ/issue/ADR，说明为何不属于当前范围；
- `waived`：有授权、期限/范围和风险接受记录。

不得只写“以后再说”后归档。P0 未修复时不能 close；P1 默认也阻断，除非有明确风险接受。P2 可以 transferred，但不能埋在即将清理的原始 review 输出里。

## 报告与保留

- 子 agent 原始输出默认临时，只返回主 agent 聚合。
- 零 finding 不创建 review 文件；在 `verification.md` 记录审核范围、revision 和“无阻断发现”即可。
- 普通 change 的 findings/disposition 合并进 `verification.md`，不按视角创建文件。
- 只有法规、合同或用户明确要求完整审计轨迹时，使用 compliance retention profile 并保留独立报告。
- `verification.md` metadata 用 `reviews` 结构化记录 charter、完成状态和可解析证据；综合 review 与已登记专项 review 均通过后才能 Close。

隔离 reviewer 的组织方式见 [review-agents.md](review-agents.md)，关闭时的压缩规则见 [close-and-retention.md](close-and-retention.md)。
