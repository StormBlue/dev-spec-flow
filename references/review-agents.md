# 并行隔离审核 agent

Phase 4 的执行机制。也可在开发期里程碑边界复用。

---

## 为什么要隔离上下文

到了审核阶段，主对话上下文里塞满了你**自己写代码的过程**：你的假设、你踩过又绕过的坑、你"这里应该没问题"的自我说服。用这个上下文去审自己的代码，等于**让作者审自己的稿**——同样的盲点会再犯一遍，bug 照样漏。

**子 agent 的上下文是全新、隔离的**：它看不到主对话历史，只拿到你给它的 charter（审核什么）+ 它自己读到的代码和 spec。于是它的判断**不被"作者视角"污染**——这正是并行审核能审出东西的根本原因。

额外好处：
- **省主上下文**：审查读大量文件，全丢给子 agent，结论才回主线程，主线程不被淹（见 [`context-and-agents.md`](context-and-agents.md)）。
- **可并发**：多个视角同时跑，比顺序快几倍。
- **专注**：一个 agent 只盯一个视角，比"一次什么都看"更深。

---

## Claude Code 能力前提（已确认）

- 子 agent（Agent/Task 工具）拥有**独立、隔离的上下文窗口**，**看不到**主对话历史。
- **一条消息里可并发派发多个**子 agent。
- 子 agent **只回传最终结论**（不是完整过程），所以 charter 要明确要求结构化输出。
- 子 agent **不能再派子 agent**；可读文件，给了写工具也能写（但审核 agent 设为**只读**）。
- 子 agent 类型：**Explore**（只读、快，适合审查）、**general-purpose**（全工具，适合需要跑命令/复现的审查）、Plan（只读、用于规划）。

---

## 审核 agent charter 模板

派发每个审核 agent 时，给它一份这样的 charter（替换 `<...>`）：

```
你是一个独立的代码审核员，只负责【<视角，如：安全>】这一个视角。你没有参与这次开发，请以挑剔的新人视角审查。

## 审核范围
- change 目录：openspec/changes/<id>/
- 本次改动的代码：<给出 git diff 范围 / 文件列表，如 `git diff main...HEAD`>

## 对照基准（真相）
- 需求与验收：读 openspec/changes/<id>/specs/ 下的 Requirement + Scenario
- 设计决策：openspec/changes/<id>/design.md（如有）

## 你这一视角要查什么
<把对应视角的清单贴进来，见下方"视角清单库">

## 输出要求（只读审查，不要改代码）
按严重程度列出 findings，每条必须含：
- 严重度：🔴 P0 / 🟡 P1 / 🟢 P2
- 位置：`文件:行号`
- 现象：具体问题
- 影响：为什么是这个级别
- 建议修复：一句话思路
若某项查完无问题，明确写"无发现"。不要为了凑数编造 finding。
最后给一句总体评估。
```

> 用 **Explore** 类型跑只读审查；需要实际跑命令复现（如性能 profiling、跑测试）的视角用 **general-purpose**。

---

## 视角清单库

每个 agent 拿其中**一项**作为它的 charter 重点。按级别选用（Lite 1-2 项 / Standard 4-5 项 / Full 8-12 项）。

| 视角 | 重点（贴进 charter） |
|------|----------------------|
| **功能正确性** | 拿 spec 的 **scenario 列表逐条核对**——每个 WHEN/THEN 真能跑通吗？happy path + 异常路径都覆盖？从用户视角能顺畅完成？ |
| **类型 & 静态分析** | 跑 `tsc --noEmit`/`pyright`/`mypy`/`cargo clippy`/`golangci-lint` 零 warning；每个 `any`/`unknown`/`as`/`# type: ignore` 都要有理由；死代码、未用导入。 |
| **性能** | DB N+1 / 缺索引 / 全表扫；前端多余重渲染 / bundle 体积 / 图片懒加载；内存泄漏（监听器/定时器/订阅未释放）；高频路径 profile。 |
| **安全** | 注入（SQL 参数化、shell escape、HTML escape、路径 normalize）；每个 endpoint 鉴权 + 水平/垂直越权；敏感数据不入日志/不泄漏客户端；依赖 CVE（`npm audit`/`pip-audit`）；CORS/CSP/CSRF。 |
| **UX & a11y** | 加载/空/错误态都像样；键盘可达 + focus 可见 + esc 关闭；screen reader（label/aria/语义标签）；对比度 WCAG AA；i18n 长文本不破、RTL；移动/平板/桌面三档。 |
| **跨模块集成** | 模块边界清晰不偷偷耦合；API/event 契约稳定、版本化；模块间错误传播合理。 |
| **回归** | 本次改动有没有波及其他功能；跑全量回归测试；手动验证最常用功能仍正常。 |
| **文档对齐** | `proposal`/`spec`/`design` 与最终实现一致？`tasks.md` 备注块写全？API 文档在？新人 onboarding 缺什么？ |
| **数据 & 迁移** | migration 可逆（有 down）；索引；事务包裹跨表写；硬删 vs 软删；老数据能读。 |
| **运维可观测** | 关键操作有日志（含 trace_id）；业务指标埋点；错误上报；依赖挂了优雅降级。 |

---

## 主 agent 的聚合-修复回路

子 agent 跑完，主 agent（你）负责收口：

```
1. 收集所有 agent 的 findings
2. 去重 / 合并（不同视角可能指向同一处）
3. 按 P0 → P1 → P2 排序，判定哪些本轮必修
4. 逐条修复（修复由主 agent 或专门的 fix agent 做——审核 agent 是只读的）
5. 修完重新跑 测试 / lint / type check，确认未引入新问题
6. 把本波结果写进 openspec/changes/<id>/review-<perspective|round-N>.md
7. commit（如 "review(security): 修复 3 处越权 + 1 处注入"）
8. 进入下一波或结束
```

**修复也可派 agent**：把"修复清单 + 文件"丢给一个 general-purpose 子 agent 去改，主 agent 只做编排和复核——进一步省主上下文。但**修复后一定要在主线程或验证 agent 里重新跑测试**确认。

---

## 与内置 review skill 的配合

并行子 agent 是"按视角深挖"，内置 skill 是"成熟的现成 pass"，二者互补：

| 内置 | 用法 | 配合方式 |
|------|------|----------|
| `/code-review [effort] [--fix] [--comment]` | 审当前 git diff 的正确性 + 清理项，自身就多 agent 并行 | 当作"功能+正确性"那一波的引擎，或最后兜底跑一遍 |
| `/security-review` | 审 pending 改动的安全漏洞 | 可替代/补充"安全"视角 agent |
| `/simplify` | 4 个并行 agent 找简化/复用/效率（不查 bug） | 归档前做一次清理 pass |
| `/verify`、`/run` | 真跑 app 验证行为 | 喂给"功能正确性"视角做运行时确认（见 [`verification.md`](verification.md)） |

---

## Codex / 无子 agent 环境的降级方案

Codex（及任何没有并行子 agent 能力的环境）拿不到"隔离上下文"，只能近似：

1. **顺序跑各视角**：一次只戴一顶帽子，把上面的视角清单当 checklist 一项项过。
2. **尽量减小污染**：理想情况下**每个视角开一次新会话**（或 `/clear` 后重进），只带上 change 目录 + diff，不带开发期的长上下文——人工模拟"隔离上下文"。
3. **显式自我提示**：每个视角开头写一句"忽略我之前写代码时的假设，以新人视角审查这部分"。
4. 其余（聚合、分级、修复、写报告、commit）与上面一致。

降级方案审出的东西会比并行隔离少，但仍远好于"用开发上下文一次性自审"。
