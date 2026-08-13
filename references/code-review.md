# 连贯 Diff 自检

在提交一个连贯实现单元前审查实际 diff。自检用于尽早发现明显问题；它不替代风险触发的独立 review，也不要求为每个机械子任务填一遍长表。

## 核心检查

### 行为与范围

- diff 是否实现它声称覆盖的 AC/BR/SC，错误与边界行为是否一致？
- 是否遗漏必要状态（失败、空、加载、权限、兼容、恢复）？
- 是否出现未批准的范围扩张、破坏性行为或与 delta spec 不一致？
- 无关格式化、生成物、调试代码、secret 和临时文件是否混入？

### 正确性与集成

- 输入边界、null/empty/extreme、错误传播和资源释放是否合理？
- 并发、幂等、事务、缓存、一致性与时区等只在相关时检查，不机械套用全部清单。
- API/event/schema 调用方与兼容性是否同步？
- 是否复用了项目模式，避免新建重复抽象？

### 类型、静态与维护性

- 是否引入无理由的不安全类型、ignore、断言、死代码或未用依赖？
- 命名、模块边界和控制流能否让下一位维护者快速理解？
- 注释解释原因而非复述代码？
- migration/feature flag/rollback 是否与实现共同交付？

### 证据

- 为本次改变选择的 evidence method 是否适合，而不是默认新增测试？
- impacted checks 是否实际运行，结果、revision 和 ref 是否写入 `verification.md`？
- 现有测试若被引用，是否有本次运行结果，而非只有测试文件路径？
- 失败或无法验证的部分是否显式暴露，而非用“应该可以”代替？

## 风险 overlay

根据 proposal 的 driver 只添加相关检查：

- security/privacy：身份、授权、注入、secret/PII、默认拒绝；
- data migration：备份、可逆性、旧数据、重入、约束与不变量；
- contract/integration：版本、兼容、消费者、错误/重试语义；
- performance/scale：代表性数据、热路径、查询与资源生命周期；
- UX/a11y：键盘/读屏、focus、状态、跨 viewport、文本溢出；
- operations：启动、配置、日志、指标、告警、降级和回滚。

详细专项触发见 [review-policy.md](review-policy.md)。

## 发现与记录

立即修复局部问题。只有以下内容需要落盘：

- 改变规格/设计/风险的事实 -> 对应 artifact；
- 下次恢复必须知道的中断点 -> task recovery/progress；
- 新证据或失败结果 -> `verification.md`；
- 无法在当前范围解决的问题 -> 稳定 REQ/issue/ADR/waiver。

不要为了证明做过自检，给每个 task 生成空备注、重复总结或 review 文件。自检后若没有 material discovery，干净 diff 与证据记录已经足够。
