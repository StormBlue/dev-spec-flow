# 复杂度与失败风险策略

流程强度由两个独立维度决定：

- **协作复杂度**决定需要多少规格、设计和计划上下文。
- **失败风险**决定验证证据、专项审核和回滚准备的强度。

大改动可以低风险，小改动也可能高风险。禁止用代码行数、任务数或 Lite/Standard/Full 标签替代风险判断。

## 协作复杂度

| 档位 | 判断信号 | 默认 artifact 深度 |
|---|---|---|
| `small` | 单一清晰意图、局部边界、一个上下文可完成 | 精简 proposal；行为改变才写 delta；tasks/design 按需 |
| `medium` | 多个依赖步骤、跨模块、需要交接或跨会话恢复 | proposal + delta + tasks；有重要技术选择时写 design |
| `large` | 多域/多团队/多 change、范围会演进、发布编排复杂 | 拆分相互可交付的 change；每个保持独立追溯；共享长期决策用 ADR |

复杂度影响“如何沟通和分解”，不自动增加测试或 reviewer。

## 失败风险

从下列 driver 评估失败后果、发生可能性、可检测性与可恢复性：

| Driver | 典型问题 | 通常需要的保障 |
|---|---|---|
| `security-privacy` | 鉴权、越权、注入、密钥、PII | 负路径证据、安全专项审核、最小权限检查 |
| `data-migration` | 数据丢失、格式转换、不可逆写入 | 迁移演练、备份/回滚、数据一致性验证 |
| `money-entitlement` | 金额、计费、库存、权限授予 | 边界/幂等/审计证据，必要时双重核对 |
| `external-contract` | 公共 API、事件、SDK、第三方契约 | 契约或兼容性验证、版本/降级计划 |
| `concurrency` | 竞态、重复提交、乱序事件 | 并发/幂等证据，失败恢复检查 |
| `availability-operations` | 启动、部署、告警、容量、依赖故障 | smoke、回滚、可观测性与故障演练 |
| `performance-scale` | 热路径、数据量、延迟或资源约束 | 有代表性负载和可复现测量 |
| `ux-accessibility` | 核心用户路径、键盘/读屏、跨视口 | 真实运行、截图/浏览器/a11y 证据 |
| `novelty` | 陌生技术、未验证假设、当前文档不足 | 有来源的探索、spike 或更早验证 |
| `wide-blast-radius` | 共享组件、平台基础设施、多消费者 | 更广回归范围和集成审核 |
| `hard-to-rollback` | 发布后难撤回或有长期副作用 | 分阶段推出、feature flag、明确恢复计划 |

### 风险等级

- `low`：局部、易发现、易回滚，失败影响有限。
- `medium`：有一个显著 driver，或影响多个消费者但可控制。
- `high`：高后果、难检测/难回滚，或多个 driver 相互放大。

在 proposal 中记录 `risk.level`、`risk.drivers` 与简短理由。不要伪造数值评分。信息不足时标 `unknown` 并用 `explore` 或早期验证降低未知。

## 决策规则

1. **最低充分保障**：选择能支持当前验收主张的最轻证据，不追求形式上的“全覆盖”。
2. **风险触发专项**：默认综合 review；只有 driver 或实际 finding 需要时追加专项 reviewer，见 [review-policy.md](review-policy.md)。

其中 `security-privacy` 是强制门禁：verification 必须登记并通过 `security/privacy`
charter，且该 review 要有 observed capture。其它 driver 仍按具体变更选择最低充分的专项
或证据，不把未知 driver 机械映射成 reviewer 数量。
3. **测试由回归价值触发**：稳定契约、缺陷复现、安全/迁移边界等优先自动化；纯文案或低价值重复路径可以用检查、运行或截图，见 [verification.md](verification.md)。
4. **先验证最危险假设**：高风险未知不应留到最后。
5. **风险可动态改变**：实现发现共享调用方、迁移或不可逆副作用时，立即更新 risk 并调整验证/review；风险降低也可取消不再必要的动作。
6. **保留强度也由义务决定**：普通 change 使用 summary retention；法规、审计或明确合规义务才使用 compliance profile，见 [close-and-retention.md](close-and-retention.md)。

## 风险摘要示例

```yaml
complexity: medium
risk:
  level: high
  drivers:
    - data-migration
    - hard-to-rollback
  rationale: "迁移会重写现有记录，失败可能导致历史数据不可读"
assurance:
  verify:
    - migration-dry-run
    - rollback-rehearsal
    - data-invariant-check
  review:
    - data-migration
```

这里记录的是选择理由，不是固定阶段或 reviewer 数量承诺。
