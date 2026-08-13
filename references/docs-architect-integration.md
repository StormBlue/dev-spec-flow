# 与 docs-architect 的单一真相协作

dev-spec-flow 管理一次 change 的澄清、实现、证据、review 和 close；docs-architect 管理跨 change 的稳定 ID、关系、影响分析、长期文档、freshness、索引和生命周期检查。两者协作时不创建两套 requirement/spec/plan。

## 检测与兼容

若仓库存在 `.docs-architect.json`、docs-architect metadata、其 Skill/CLI 或明确项目约定，则启用集成；先读取实际 schema 和工具能力，不假定版本。

- 能完整集成：复用 metadata、ID、relations、status 与 `check/impact/index`。
- 只能部分集成：保持本映射和稳定 ID，运行可用检查，记录缺少的能力。
- 未安装：dev-spec-flow 可独立运行；不要擅自初始化 docs-architect 或创建 `docs/requirements`。

## Artifact 映射

| dev-spec-flow 路径 | docs-architect 类型/角色 | 真相约束 |
|---|---|---|
| `openspec/changes/<slug>/proposal.md` | `requirement` | 唯一动机、验收和生命周期记录 |
| `openspec/changes/<slug>/tasks.md` | `exec-plan` | 唯一持久执行/恢复计划 |
| `openspec/specs/<domain>/spec.md` | active `product-spec` | 唯一当前产品行为真相 |
| change 内 delta spec | 临时增量 | 不登记为第二份 active product-spec |
| `design.md` | change-local design | 跨 change 的长期决定提升为 `decision`/ADR |
| `verification.md` | `evidence` manifest | 只引用可检查 proof，不复制 assertion |
| `docs/`、`ARCHITECTURE.md` | `system-doc` | 当前架构、使用、操作和约束 |

如果 docs-architect 配置默认路径与上述路径冲突，优先配置 artifact locations/扫描范围；不要复制 proposal 到 `docs/requirements` 或复制 tasks 到另一 execution-plan 目录。

## Metadata 与关系

复用 docs-architect 当前 schema 要求的 envelope。建议关系方向：

- tasks/plan `implements -> REQ`；
- evidence `validates -> REQ` 或相关 spec；
- product/system docs `documents -> REQ`；
- design/ADR `derives_from -> REQ`；
- dependency 使用 `depends_on`；
- generated index 使用 `generated_from`。

BR/SC/AC/task 的细粒度 ID 可保存在 artifact 正文或 schema 允许的字段里；不要塞入 validator 不认识且会报错的字段。schema 扩展前以当前工具为准。

origin 与 approval 分开：用户请求、issue 或旧文档可以是 origin；进入 accepted/后续状态的 approval 必须指向 docs-architect 接受的可解析 authority record。实现存在、agent 断言和沉默不构成批准。

## 开发期握手

### Intake/propose

1. 搜索 docs index 与 active/archive，分配/复用 REQ ID。
2. proposal 作为 requirement；tasks 作为关联 exec-plan。
3. 主 spec 是 product-spec；delta 只通过关系引用目标 SPEC/BR。
4. 记录 sources/affected_code/update_when 等当前 schema 支持的影响锚点。

### Apply/update

1. 改动路径变化时运行/模拟 impact traversal。
2. 只更新确认受影响 artifact；低置信语义候选保持 advisory。
3. 实际 evidence 写入 verification，并在 requirement acceptance/top-level evidence 按 schema 引用。
4. 重要跨 change 决策提升为 ADR，避免 design 与 ADR 双写全文。

### Close

按 [close-and-retention.md](close-and-retention.md)：

```text
readiness
 -> merge delta to product-spec
 -> docs-architect impact + sync
 -> update active system/product docs OR evidenced no_change_required
 -> close requirement/plan/evidence lifecycle
 -> compress registered temporary artifacts and archive
 -> check -> index --write -> check
```

`documentation_disposition: updated` 应由实际受影响且当前有效的 product/system doc 支持；若当前 docs-architect 版本只接受 system-doc，则按其真实 gate 执行并明确记录兼容限制，不用虚假文档改动绕过。`no_change_required` 必须有 reviewed scope、具体理由和捕获证据。

执行 change 的 agent 负责解析当前 docs-architect Skill 路径，运行 impact/check/index，并把捕获结果登记到 verification metadata 的 `documentation_checks`。dev-spec-flow CLI 只校验这些结果及 disposition 的结构门槛，不猜测另一个 Skill 的安装路径，也不擅自初始化 docs-architect。

## 责任边界

- dev-spec-flow 不重实现 docs_guard 的 schema/link/index 校验。
- docs-architect 的结构 check 不证明代码/行为通过；行为证据仍由 verification 提供。
- docs-architect garden 不替代每个 change 的即时 close/retention。
- adapter/索引是导航，不是 requirement/spec 的第二真相源。
- 集成失败时报告具体 gate；不要悄悄跳过并声称归档完成。
