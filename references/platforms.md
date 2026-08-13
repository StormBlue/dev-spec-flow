# 平台适配与能力检测

工作流政策应只有一份 canonical source。Claude、Cursor、Codex、Grok 的入口是薄 adapter，负责让平台发现同一套规则，不复制并逐渐漂移出另一份流程。

## Canonical 与 Adapter

- `SKILL.md`：平台中立的动作路由与必守不变式。
- `references/`：本文档集，拥有细节政策。
- 平台入口（如 `AGENTS.md`、Claude skill、Cursor rules、Grok skill）：只说明触发、路径解析、如何调用当前能力。
- 包级 `manifest.json` 记录 canonical 与 adapter 的来源版本/hash；修改 runtime 文件后校验整个包的 parity。
- update/doctor 在任何替换或删除前，必须将安装记录的 package version、manifest hash、文件集合和逐文件 hash 与已安装的历史 manifest 完整核对；删除集合还必须限制在该历史 manifest 明确拥有的路径内。
- 用户修改过的 adapter 不自动覆盖/删除；update/doctor 报告漂移并给出安全处理方式。

这套校验提供受管文件的 ownership 和本地一致性保证，不是发布包真实性证明。能同时改写安装记录与历史 manifest 的主体可以伪造一份自洽历史；抵御该威胁需要签名、可信 registry 元数据或其它外部 trust anchor。文档与 doctor 输出不得把当前能力表述成 authenticity guarantee。

## 运行时能力检测

每次任务依据当前会话实际工具选择机制：

| 能力 | 有时 | 没有时 |
|---|---|---|
| 隔离子 agent | 并行独立探索/专项 review | 主上下文聚焦执行，必要时新会话 |
| 计划/审批 UI | 用于真正需要授权的决策 | 普通对话提出一个具体问题 |
| Web/官方文档工具 | 核实版本敏感事实 | 本地文档/CLI；无法核实标 unknown |
| 浏览器/应用控制 | 取得 runtime/UI evidence | 使用项目测试或给出明确未验证缺口 |
| 内置 review/security skill | 作为风险专项的实现引擎 | 用本仓库 charter/checklist |
| docs-architect/guard | impact/check/index 自动化 | 保持映射，手工校验并报告限制 |

不要根据产品名称声称“有/没有子 agent、hooks、slash command、递归委派”等。能力会随版本、插件和宿主变化。

## 路径解析

adapter 必须把 reference/template 链接解析到实际安装位置：

- skill 目录安装：相对 `SKILL.md` 解析；
- vendored `.dev-spec-flow/`：以该目录为根；
- 根 `AGENTS.md` 只引用 vendored canonical 文件，不粘贴全部正文；
- 若路径不可读，明确说明缺失并使用最接近的安全规则，不发明内容。

## 平台不变式

无论平台能力如何，下列结果不降级：

- 稳定 REQ/BR/SC/task ID 与真实生命周期时间；
- Scenario 作为验收锚点而非自动化测试配额；
- 风险驱动 evidence/review，不用固定 agent 数量；
- active change 完成后执行原子 close 与及时归档；
- docs-architect 启用时保持单一真相；
- 保留用户改动，破坏性/外部动作遵守授权。

执行机制可以顺序或并行，证据方法可以因工具不同而改变；不能用平台限制伪造验证成功。

## 支持矩阵的写法

README/doctor 只陈述已实测事实，并注明版本/日期。建议区分：

- discovery/trigger；
- canonical reference loading；
- isolated agents/concurrency；
- browser/runtime evidence；
- hooks/automation；
- update/doctor/parity check。

未知写 `unknown/not verified`，不把单次环境观察泛化为整个平台永久能力。
