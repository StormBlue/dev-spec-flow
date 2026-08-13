<!-- docs-architect-meta {"schema_version":1,"id":"SYS-dev-spec-flow-guide","type":"system-doc","title":"dev-spec-flow user and maintainer guide","status":"active","owners":[],"sources":["README.md","SKILL.md","manifest.json","scripts/dev_spec_flow.py","adapters/**"],"update_when":["Installation, platform support, CLI commands, migration, or release behavior changes"],"relations":[{"type":"documents","target":"REQ-2026-001"}],"evidence":[],"affected_docs":[],"verified_at":null,"verified_against":null} -->

# dev-spec-flow

面向全栈工程的规范驱动开发 Skill。它把模糊需求组织成 OpenSpec 风格的 change，以风险选择调研、设计、验证和专项审核，持续完成实现，最后同步长期文档并原子化归档。

核心模型不是固定阶段，而是一组可组合动作：

```text
intake -> explore? -> propose/update -> apply -> verify? -> close
```

`?` 表示由未知程度或失败风险触发。清晰的小改动不会被强制要求完整设计、逐 Scenario 新增测试或多轮审核；安全、迁移、外部契约等高风险改动仍会获得相应强度的证据和专项审查。

## 主要变化

- **双轴策略**：协作复杂度决定文档详细程度，失败风险决定验证和 Review 强度。
- **Evidence plan**：Scenario 是验收示例，可由已有测试、自动化测试、命令、运行时检查、人工检查或截图证明。
- **风险触发 Review**：默认一次综合审查；安全、迁移、性能、UX/a11y、集成和运维风险才追加专项视角。
- **单一验证记录**：默认只保留 `verification.md`，不为每个 reviewer 生成永久报告。
- **原子 Close**：合并 delta、同步长期文档、压缩临时材料、写时间并归档是一个完成动作。
- **稳定时间线**：REQ/AC/BR/SC/T 使用稳定 ID；生命周期使用 ISO 8601 字段和状态历史。
- **跨平台 canonical Skill**：Claude、Cursor、Codex、Grok 共享同一个 `SKILL.md`，运行时探测并行、子 Agent、浏览器等能力。
- **可执行治理**：标准库 CLI 提供 `new/status/verify/close/validate/install/update/doctor`。

## 产物模型

```text
openspec/
├── specs/<domain>/spec.md                  # 当前可观察行为
└── changes/
    ├── <slug>/
    │   ├── request.md                      # 需要持久化用户授权时创建
    │   ├── proposal.md                     # requirement + 生命周期元数据
    │   ├── specs/<domain>/spec.md          # 临时 delta
    │   ├── design.md                       # 按需
    │   ├── tasks.md                        # execution plan
    │   ├── verification.md                 # 唯一 evidence manifest
    │   └── evidence/*                      # verification 引用的实际观察 capture
    └── archive/<date>-<req-id>-<slug>/
```

主规格按稳定 `BR-*` 条款 ID merge，而不是按可改名的标题定位。目录名便于阅读，真实顺序来自 `created_at/completed_at/archived_at`。

## 快速开始

运行环境只要求 Python 3.10+，核心 CLI 不依赖第三方包。

```powershell
python scripts/dev_spec_flow.py validate
python scripts/dev_spec_flow.py install --target codex --scope user
python scripts/dev_spec_flow.py doctor --target codex
```

在目标项目中创建 change：

```powershell
python <skill-root>/scripts/dev_spec_flow.py --root <project> new add-team-todo `
  --title "Add team todo" --complexity medium --risk-level medium `
  --domain collaboration --approved --request "用户确认的原始需求"
```

开发期间和收口时：

```powershell
python <skill-root>/scripts/dev_spec_flow.py --root <project> status
python <skill-root>/scripts/dev_spec_flow.py --root <project> verify --change add-team-todo
python <skill-root>/scripts/dev_spec_flow.py --root <project> verify --change add-team-todo --readiness
python <skill-root>/scripts/dev_spec_flow.py --root <project> close add-team-todo --dry-run
python <skill-root>/scripts/dev_spec_flow.py --root <project> close add-team-todo
```

CLI 不会替 Agent 写需求内容。`new` 负责稳定 ID、时间和模板；Agent 仍需根据真实需求维护 proposal/spec/tasks/verification/evidence。明确的命令式用户请求只授权其明示范围；若没有 durable authority，`request.md` 固化该授权，不会把“请分析/调研/提案”扩成实现、commit、push 或发布许可。

## 平台安装

| 平台 | 用户级默认路径 | 项目级默认路径 | 说明 |
|---|---|---|---|
| Codex | `~/.codex/skills/dev-spec-flow` | `.agents/skills/dev-spec-flow` | 本机用户级路径已验证；项目级能力以运行时发现为准 |
| Claude Code | `~/.claude/skills/dev-spec-flow` | `.claude/skills/dev-spec-flow` | 使用标准 `SKILL.md` 包 |
| Cursor | `~/.cursor/skills/dev-spec-flow` | `.cursor/skills/dev-spec-flow` | 使用标准 Skill；项目规则只作薄发现入口 |
| Grok | 显式 `--dest` | 显式 `--dest` | 默认路径和高级能力未可靠核实，不作猜测 |

安装器只复制 canonical Skill 包，不覆盖目标项目已有的 `AGENTS.md`、`CLAUDE.md` 或 Cursor rules。需要项目级发现入口时，参考 `adapters/` 中的薄模板，按目标项目现有文件做合并。

安全更新采用发布清单、安装时记录、历史 manifest 和当前文件的 ownership/hash 校验。只有历史受管文件与安装记录完整一致、且当前文件仍等于安装记录时才自动替换或删除；用户改过的文件会报告冲突并保留。该机制提供本地 ownership/integrity，不提供发布真实性证明；后者需要签名或可信 registry。

```powershell
python scripts/dev_spec_flow.py update --target codex --scope user
python scripts/dev_spec_flow.py doctor --target codex --json
```

## 与 docs-architect 配合

两套 Skill 不维护两套真相：

| dev-spec-flow 文件 | docs-architect 角色 |
|---|---|
| `proposal.md` | requirement |
| `tasks.md` | exec-plan |
| `openspec/specs/<domain>/spec.md` | 唯一 active product-spec |
| change 内 delta spec | 临时增量，不登记为第二份 product-spec |
| `verification.md` | evidence manifest |
| `docs/`、`ARCHITECTURE.md` | system-doc |

dev-spec-flow 管一次 change 的执行、证据、收口和归档；docs-architect 管长期文档影响、关系、freshness、索引和 garden。检测到 `.docs-architect.json` 时，执行 change 的 agent 先运行 docs-architect 的 impact/check/index 流程并把结果写入证据清单；Close CLI 校验文档处置和捕获证据已经满足，不猜测另一个 Skill 的安装路径。完整契约见 [docs-architect-integration.md](references/docs-architect-integration.md)。

## 从旧版本升级

旧版本可能同时存在根 `AGENTS.md`、项目 `.dev-spec-flow/` 和用户级 Skill 副本。先运行：

```powershell
python scripts/dev_spec_flow.py doctor --root <project>
```

迁移原则：

1. 安装新的 canonical Skill 包。
2. 把旧 `AGENTS.md` 中真正属于项目的命令和约束留下；删除重复的工作流正文。
3. 只有 hash 未被用户修改的托管文件才允许更新或移除。
4. 旧 active change 保持可读，在下一次实际更新或 Close 时增量补元数据。
5. 无法证明的历史时间标为 unknown 或 `git-inferred`，不伪造精确时间。

## 仓库结构

```text
SKILL.md                         canonical runtime policy
AGENTS.md                        本仓库薄适配器
agents/openai.yaml               Codex UI metadata
references/                      按需加载的详细规则
templates/                       change artifact 模板
adapters/                        可选项目级薄发现模板
scripts/dev_spec_flow.py         零依赖 CLI
tests/test_dev_spec_flow.py      生命周期与安装安全测试
manifest.json                    发布文件 hash 清单
```

开发本 Skill 时运行：

```powershell
python -m unittest discover -s tests -v
python scripts/dev_spec_flow.py validate
python scripts/dev_spec_flow.py doctor --root .
```

修改 runtime 文件后，由维护者执行 `validate --refresh-manifest` 更新清单，再重新运行全部测试和 validate。

## 设计依据

- [OpenSpec](https://github.com/Fission-AI/OpenSpec)：actions、artifact DAG、delta specs 与 archive。
- [GitHub Spec Kit](https://github.com/github/spec-kit)：测试和 analyze/checklist 作为按需能力。
- [Agent Skills](https://agentskills.io/) 与 [AGENTS.md](https://agents.md/)：canonical Skill、渐进披露与薄项目指令。
- [Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)：按价值选择测试层级并避免重复覆盖。
- [Diataxis](https://diataxis.fr/) 与 ADR practices：分离当前真相、决策和过程材料。

本项目不把任何单一框架当成银弹。目标是用最小但足够的结构减少返工、遗漏、验证噪声和未归档 change。
