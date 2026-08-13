# 隔离审核执行机制

独立上下文能减少作者假设带来的盲点。这里仅说明如何执行隔离审核；审哪些视角、如何处置 finding 由 [review-policy.md](review-policy.md) 决定。

## 先检测能力

不要根据“Claude/Codex/Cursor/Grok”名称硬编码能力。检查当前会话实际是否提供：

- 可创建隔离上下文的子 agent；
- 并发执行与只读权限；
- 可运行命令、浏览器或应用的 reviewer；
- 内置 code/security review 或验证工具；
- 可用的上下文与并发额度。

有隔离 agent 时派发；没有时在当前上下文做一次明确切换视角的综合 review，或在可行时使用新会话。能力差异不改变质量 gate，只改变执行机制。详见 [platforms.md](platforms.md)。

## 派发原则

1. 默认只派一个综合 reviewer；风险策略要求专项时再增加对应 reviewer。
2. 能并行且视角互不依赖时并行；需要综合结果后才决定的专项顺序执行。
3. reviewer 默认只读。需要跑复现/测量命令时明确授权范围；修复由主 agent 或单独 fix task 完成。
4. 给 reviewer 最小充分上下文，不传开发过程的自我解释：change 目录、目标 diff、相关项目规则、主 specs 与明确 charter。
5. 原始输出只回传 findings，不直接创建 `review-*.md`。

## 通用 charter

```text
你没有参与本次实现。请以独立 reviewer 身份审查这个 change。

范围：
- change: openspec/changes/<slug>/
- diff: <base...head 或明确文件>
- 当前行为真相: openspec/specs/<相关 domain>/

视角：<综合，或由风险触发的专项视角>

要求：
1. 对照 AC、BR/SC、项目约束和 verification evidence。
2. 不因测试通过而推定实现正确；也不要无理由重跑已有可信验证。
3. 每个 finding 给 severity、文件:行、现象、影响、违反的锚点和建议方向。
4. 只报可行动问题，不凑数。无阻断发现时明确说明范围与残余风险。
5. 只读，不修改文件；除非任务明确授权复现命令。
```

专项 charter 只加入该风险相关的检查，不复制整套通用 checklist。

## 聚合与修复

主 agent 负责：

1. 合并重复 findings，验证位置与严重度，不照单全收。
2. 将确认的问题映射到 AC/BR/项目约束。
3. 按 P0/P1/P2 和依赖顺序修复；修复后只运行受影响的验证。
4. 将最终 finding disposition 与新增证据写入 `verification.md`。
5. 必要时追加一次聚焦 re-review；不因“第二波”模板而重复全量审核。
6. 确保 transferred/waived 项有稳定引用，再允许 close。

若使用 fix agent，给它一个边界清晰的 finding 集；主 agent 仍负责复核 diff 与证据。

## 上下文卫生

- reviewer 只需要 current specs、change artifact、diff 和项目规则；不要灌入原始调研聊天。
- 输出限制为高信号 findings、无发现范围和残余风险。
- 审核完成后，原始 prompt/output 默认不归档；需要长期保留的事实进入 verification、REQ、issue 或 ADR。
- 并发 agent 共享工作树时 reviewer 不写文件，避免覆盖实现者或其他 agent 的改动。
