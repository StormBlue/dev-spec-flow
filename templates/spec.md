# Delta Spec — <capability 名>

> 复制到 `openspec/changes/<change-id>/specs/<capability>/spec.md`。
> 这是对真相源 `openspec/specs/<capability>/spec.md` 的**增量**，不重述整份 spec。
> 完整规则见 [`references/openspec-model.md`](../references/openspec-model.md) 第四、五节。
>
> 硬规则：
> - 每条 `### Requirement:` 用 SHALL/MUST（RFC 2119），描述**可观察行为**，不写实现。
> - 每条 Requirement **至少一个** `#### Scenario:`，**正好 4 个井号**，用 WHEN/THEN。
> - 每个 scenario 都是一个潜在测试用例（见 `references/verification.md`）。
> - 非功能需求（性能/安全/a11y）也写成可测 Requirement。
> - greenfield 首个 change：基本全是 `## ADDED`。

---

## ADDED Requirements

### Requirement: <能力名，如 用户可导出数据>
系统 SHALL <做什么>。

#### Scenario: <场景名，如 导出成功>
- **WHEN** <触发条件>
- **THEN** <预期结果>
- **AND** <附加结果，可选>

#### Scenario: <异常场景，如 无数据时导出>
- **WHEN** <...>
- **THEN** <...>

---

## MODIFIED Requirements

> 必须**整条粘贴** requirement 的完整新内容（从 `### Requirement:` 到所有 scenario），头部文字与 `openspec/specs/` 中原文一致。只写片段会在归档时丢细节。

### Requirement: <已有 requirement 名>
系统 MUST <改后的完整行为>。（原为：<简述原行为>）

#### Scenario: <...>
- **WHEN** <...>
- **THEN** <...>

---

## REMOVED Requirements

> 必须写 Reason + Migration。

### Requirement: <要废弃的 requirement 名>
**Reason**: <为什么废弃>
**Migration**: <现有用户/数据怎么迁移>

---

## RENAMED Requirements

> 仅改名时用。

- FROM: `### Requirement: <旧名>`
- TO: `### Requirement: <新名>`
