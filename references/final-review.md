# 最终审核 Playbook（Phase 4）

所有任务 ✅ 后跑这个流程。**执行机制**（怎么派发并行隔离子 agent、charter 模板、聚合-修复回路、Codex 降级）见 [`review-agents.md`](review-agents.md)——本文件只讲**审什么、按级别审几波、怎么收口**。

核心改变：不再用"写了一肚子代码的主上下文"去顺序自审，而是**一波并发派出多个只读子 agent，每个独立干净上下文专攻一个视角**。同样的人力换来更快 + 更少偏见。

---

## 按级别缩放

| 级别 | 波数 | 每波视角（从 [`review-agents.md`](review-agents.md) 的视角清单库选） |
|------|------|----------------------------------------------------------------------|
| **Lite（小）** | 1 波 | 功能正确性 +（最相关的一项：安全 或 UX） |
| **Standard（中）** | 1 波（4-5 agent 并发） | 功能正确性 / 类型 & 静态 / 性能 / 安全 / UX & a11y |
| **Full（超大）** | 2-3 波 | 第一波同 Standard；第二波：跨模块集成 / 回归 / 文档对齐 / 数据 & 迁移；第三波（按需）：运维可观测 / 性能压测 / i18n & a11y 深度 |

**风险驱动，不是凑数**：波数和视角是下限参考。该项目风险大的维度多派一个 agent，不相关的维度（如纯后端任务的 a11y）可省。**0 发现也如实记一句，但不要为了填表编造 finding**。

---

## 每一波的节奏

```
对每一波 W：
  1. 用户已在 Phase 0 同意按级别审，所以不再问"继续吗"
  2. 并发派发本波的视角 agent（见 review-agents.md 的 charter 模板）
     —— 每个 agent：独立上下文、只读、拿 spec/scenario 当对照基准
  3. 收齐所有 agent 的 findings → 聚合 / 去重 / 按 P0/P1/P2 分级
  4. 逐条修复（可再派 fix agent；审核 agent 是只读的）
  5. 重新跑 测试 / lint / type check，确认未引入新问题
  6. 写报告 openspec/changes/<id>/review-<perspective|wave-N>.md（模板见 templates/review-report.md）
  7. commit（如 "review(wave-1): 修复 5 处 P0/P1"）；按 git-flow 的里程碑规则 push
  8. 立刻进入下一波，不停
```

**只在最后一波跑完后**，向用户汇报全部审核总结，然后进 Phase 5 归档。

---

## 必做的闭环：scenario 逐条核对

**功能正确性**那个 agent 不是"看看代码"，而是拿 `openspec/changes/<id>/specs/` 里所有 `#### Scenario` 列成清单，**逐条确认 WHEN/THEN 真能跑通**（用 `/verify` / `/run` / 手动，见 [`verification.md`](verification.md)）。

这是需求↔审核闭环的最后一环：spec 写了 N 个 scenario，审核就要核对 N 个，一个不漏。覆盖不到的（如需真实第三方环境）明确标"未验证 + 原因"。

---

## 用内置 skill 加力

并行子 agent 之外，按需编排内置 skill 作为成熟现成 pass：

- `/code-review`（自身多 agent、可 `--fix`）——当"功能+正确性"波的引擎，或最后兜底一遍
- `/security-review`——替代/补充"安全"视角
- `/simplify`——归档前做一次清理 pass（只清理不查 bug）
- `/verify` / `/run`——喂给功能视角做运行时确认

---

## 一个轮次报告示例

```markdown
# Review 性能视角 — add-team-todo

**日期**: 2026-06-01
**视角**: 性能
**范围**: git diff main...HEAD 全部改动
**对照**: openspec/changes/add-team-todo/specs/ 的 Requirement/Scenario

## 发现

### 🔴 P0
1. `GET /api/todos` 没分页，全表返回（已 5 万行）
   - 位置: `src/api/todos.ts:14`
   - 影响: 列表页随数据增长线性变慢，违反 R-perf-1（p95<300ms）
   - 修复: 加 cursor 分页

### 🟡 P1
2. 看板列未虚拟化，500 卡时掉帧
   - 位置: `src/board/Column.tsx:30`
   - 修复: react-virtual

### 🟢 P2
3. ...（可留到下一里程碑）

## 修复
| Finding | Commit | 状态 |
|---------|--------|------|
| #1 分页 | `1a2b3c4` | ✅ |
| #2 虚拟化 | `5d6e7f8` | ✅ |
| #3 | — | ⏸️ 留到下期 |

## 修复后验证
- [x] 原本通过的测试仍通过
- [x] 改动跑了 lint / type check
- [x] R-perf-1 的 scenario 重新跑：万行分页 p95 = 180ms ✅

## 总结
共 3 个（P0×1 / P1×1 / P2×1），已修 2 留 1。
```

---

## Codex / 无并行环境

无子 agent 时按视角**顺序**跑、理想情况每视角开新会话减小污染，其余一致。详见 [`review-agents.md`](review-agents.md) 末尾的降级方案。
