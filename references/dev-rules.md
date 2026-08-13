# Apply：交付原则

这些原则约束实现质量，但不把每个 task 变成固定仪式。执行节奏见 [workflow.md](workflow.md)，保障强度见 [risk-policy.md](risk-policy.md)。

## 1. 项目约定优先

遵守最接近目标文件的项目指令、格式化/静态检查、命名、目录、测试和 Git 约定。修改前阅读相似模块；优先复用本地 helper、组件、抽象和错误模型。

通用建议与项目约定冲突时：安全底线和用户明确要求优先，其余跟项目走。不要借新 feature 顺手重写无关模块。

## 2. 保持类型与边界清晰

- 使用项目已有的类型系统和严格度，不新增无理由的 `any`、裸 `Object`、忽略指令或不安全断言。
- 对外部输入、反序列化、网络/文件数据在边界验证；内部代码依赖验证后的类型。
- 公共 API、错误和 nullability 与现有契约一致。
- 若历史代码无法一次消除不安全类型，局部隔离并说明原因，不把范围扩大成全面重构。

## 3. 依赖遵循项目策略

新增依赖前确认确有价值、许可证/维护/安全可接受，并核对当前官方接口。

- 保持项目现有 manifest 语义（精确版本或合法 range）和 lockfile 策略。
- 不为“最新”盲目升级无关依赖，也不手工伪造 lockfile。
- 用户要求升级或安全修复时，选择与运行时/框架兼容的当前稳定版本，并运行相应验证。
- 新依赖、运行时要求和回滚影响记录到 design/proposal；长期 setup 变化同步系统文档。

## 4. 注释解释原因

注释语言、风格和 docstring 约定跟随项目。没有约定时使用当前任务/仓库主要语言，保持简洁。

只注释反直觉原因、隐含约束、兼容性/安全考虑和无法由类型表达的事实。不要复述代码。长期设计理由属于 ADR/design，不塞进大段源码注释。

## 5. 维持可理解的结构

文件大小不是固定质量门槛。出现以下信号时才拆分：多重职责、频繁冲突、难以独立测试/理解、条件嵌套失控、重复逻辑或已有项目阈值被违反。

拆分应服务当前改动并保持行为，不因达到任意行数就制造抽象。生成文件、迁移、schema、声明式配置等按项目惯例处理。

## 6. 同步 durable truth

实现发现事实变化时更新对应所有者：

- 意图、范围、AC、风险 -> proposal；
- 可观察行为 -> delta spec；
- 技术权衡、迁移/回滚 -> design 或长期 ADR；
- 顺序、依赖、恢复点 -> tasks；
- 实际验证 -> verification；
- 当前系统/命令/运维事实 -> system docs。

只记录能帮助验收、恢复或未来维护的事实；不要求每个 task 填“遇到的问题/实现逻辑/关键决策”空模板。与 docs-architect 的同步见 [docs-architect-integration.md](docs-architect-integration.md)。

## 7. 验证是证据，不是测试配额

每个验收主张都要有足够证据，但方法按风险与回归价值选择。运行 impacted checks，记录真实结果，避免在 task、里程碑、review 和 close 四次重复同一套验证。完整策略见 [verification.md](verification.md)。

## 8. UI 服从现有体验与用户需求

先检查现有 design system、组件和相似流程。新体验或设计未知才调研/确认；局部修复直接沿用项目模式。响应式、状态完整性与 a11y 是可观察验收，不是最后装饰。见 [ui-design.md](ui-design.md)。

## 9. 保持动量，尊重授权

一个 task 完成后继续选择 ready task，不因固定阶段或内部检查反复请求确认。只有 workflow 中定义的真实歧义、外部决策、破坏性操作、持续失败或外部不可用才暂停。

持续执行不扩大授权：发布、push、创建外部资源、删除数据或覆盖用户文件仍需用户请求或项目明确许可。

## 单个实现单元的最小循环

```text
select ready task
  -> mark in_progress
  -> implement coherent change
  -> impacted verification + diff self-review
  -> update only changed truth and material recovery notes
  -> mark completed when evidence supports it
  -> commit according to project/user Git policy
  -> select next ready task
```

这是可恢复循环，不要求一个 task 必须等于一个测试、一个 reviewer 或一个 commit。
