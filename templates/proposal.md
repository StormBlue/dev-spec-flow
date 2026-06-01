# Proposal — <Change 标题>

> 复制到 `openspec/changes/<change-id>/proposal.md`，替换所有 `<...>`。
> 保持精炼（1-2 页），聚焦 **why 与 what**，实现细节留给 `design.md`。
> 写法说明见 [`references/openspec-model.md`](../references/openspec-model.md) 第三节。

**Change ID**: `<add-team-todo>`
**级别**: Lite / Standard / Full
**状态**: 草稿 / 评审中 / 已确认 / 实施中 / 已交付 / 已归档
**日期**: <YYYY-MM-DD>

---

## Why

<要解决的问题 / 机会，1-2 句。为什么是现在？谁受益？>

## What Changes

<要做的改动清单，具体到能让人判断范围。破坏性改动标 **BREAKING**。>

- <改动 1>
- <改动 2>
- **BREAKING** <破坏性改动，如有>

## Capabilities

> 这一节是 proposal 与 spec 阶段的契约：这里列几个能力，spec 阶段就产出对应几个 `specs/<name>/spec.md`。先查 `openspec/specs/` 已有的名字。

### New Capabilities（新建）
- `<kebab-name>`: <这个能力覆盖什么>

### Modified Capabilities（改已有 requirement，仅 spec 级行为变化时列）
- `<existing-name>`: <哪条 requirement 怎么变>

## 范围

**In scope（本次要做）**
- ✅ <...>

**Out of scope（本次不做，写出来避免误解）**
- ❌ <...>

## 成功标准

<怎么算做完了？尽量可度量。>

- <用户能完成 X 主流程，全程不报错>
- <p95 < 200ms / 崩溃率 < 0.1% / ...>

## Impact

<影响的代码 / API / 依赖 / 数据 / 外部系统。新增依赖在此点名，详细版本进 design。>

## 开放问题 / 待用户拍板

- [ ] <选 A 还是 B？（影响什么）>
- [ ] <需要哪个第三方资源 / 密钥？>
