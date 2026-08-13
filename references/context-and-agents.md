# 上下文、断点续做与 Agent 协作

长任务依赖磁盘上的稳定状态，而不是聊天记忆。目标是用最少的持久信息恢复正确下一步，并让临时 agent 输出在 Close 时被压缩。

## 真相层级

1. proposal 的机器可读 metadata：requirement 身份、生命周期、时间、风险和验收。
2. `tasks.md`：task ID、依赖、优先级、状态、恢复点与 outcome。
3. delta spec/design：行为变化与技术决策。
4. `verification.md`：实际证据与 finding disposition。
5. Git status/diff/log：工作树和提交事实。
6. 会话 Todo 或聊天总结：仅当前执行提示，不能覆盖上面真相。

emoji、派生进度表和文件顺序不是机器状态。若它们与 metadata/task 字段冲突，以结构化字段和实际 Git 状态为准并修正文档。

## 断点续做协议

```text
1. 定位 active REQ/change，读 proposal metadata 与目标
2. 读 tasks，若有 in_progress task 优先恢复
3. 检查 git status/diff，核对 task recovery note 与实际工作树
4. 若无 in_progress，计算 depends_on 全完成的 ready tasks
5. 选择最高 priority；同优先级按稳定 task ID
6. 只读该 task 关联的 AC/BR/SC、design 段落和证据缺口
7. 继续 apply 循环
```

如果 change 处于 close 中断，按 [close-and-retention.md](close-and-retention.md) 的幂等恢复协议处理，不从普通 task 重新开始。

## 只记录 material 状态

task 的 progress/recovery 记录：

- 当前完成到哪个可检查边界；
- 未提交 diff 的意图；
- 已运行命令和失败原因（详细证据可链接 verification）；
- 下一步和外部阻塞条件；
- 会改变后续实现的重要发现。

不要求每个完成 task 填相同的“问题/实现/决策”三栏。无新事实时只更新 status/outcome/commit mapping。

## 使用子 Agent

在当前环境实际提供隔离 agent 且并行能提升速度/质量时，用于：

- 针对独立问题的代码/文档探索；
- 风险触发的只读专项 review；
- 相互不写同一文件的实现子任务；
- 长输出可压缩为短结论的调研。

给 agent 明确 scope、可读文件、允许的命令/写权限、输出格式与不应触碰的用户改动。共享工作树时避免多个 writer 编辑同一文件；reviewer 默认只读。

不要断言某平台的 agent 一定能/不能再委派、并行或运行工具。运行时检测见 [platforms.md](platforms.md)。

## 上下文卫生

- 用渐进披露：先读 proposal/tasks，再读当前关联段落和源码。
- 子 agent 只回高信号结论；原始 prompt/output 默认临时。
- 搜索/调研结论吸收到 proposal/design/ADR 后，不重复携带原始摘录。
- review 读取 change、diff、主 specs 和项目规则，不继承作者的辩护性叙述。
- close 前将未解决事项提升到稳定 artifact，再删除临时材料。

## 与原生计划/Todo 的分工

平台 Todo/plan 可以镜像当前几个动作，但 `tasks.md` 才是跨会话执行计划。只在一个地方维护持久状态；计划工具更新不能代替 change artifact 更新。
