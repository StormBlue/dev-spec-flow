# 原子 Close 与保留策略

`close` 把已实现 change 变成当前真相，并立即清理 active 区。只有所有 gate 成功后才能向用户声称完成。

## 完成 gate

开始 close 前确认：

- requirement 意图与批准范围已达成；
- 所有必要 task 完成，或取消项有授权和解释；
- AC/SC 证据满足 [verification.md](verification.md)；
- review findings 已按 [review-policy.md](review-policy.md) 处置；
- delta 与最终实现一致，没有与其他 active change 的未解决冲突；
- 文档影响和长期决策已识别；
- 外部发布不被错误等同于代码完成，若发布属于验收则有实际证据。

## Close 事务

把下面步骤视为一个逻辑事务；用户和仓库政策授权 commit 时，再形成一个连贯 Git 提交：

1. **建立断点**：在 `verification.md` 记录 close attempt、目标 archive 路径和当前 revision；requirement 保持 `verifying/documented`，尚不标 `done`。
2. **readiness check**：检查 AC/evidence、tasks、findings、开放问题、依赖与 delta 冲突。失败即停止，保留明确缺口。
3. **merge delta**：按 BR/SC 稳定 ID 应用 ADDED/MODIFIED/REMOVED/RENAMED 到 `openspec/specs/`，再验证无重复、悬空或冲突。
4. **同步长期知识**：运行 docs impact；更新 product/system docs，提升跨 change 决策为 ADR，或记录有证据的 `no_change_required`。见 [docs-architect-integration.md](docs-architect-integration.md)。
5. **压缩 change**：按 retention profile 提升、压缩或删除临时材料；生成最终 verification/completion 摘要。
6. **预校验**：运行项目必要门禁、链接/metadata 检查和 index preview。不要用结构检查代替行为证据。
7. **完成生命周期**：写 `completed_at`，追加 status history 并将 requirement/plan/evidence 置为相应完成状态。
8. **移动归档**：移到 `changes/archive/<YYYY-MM-DD>-<REQ-ID>-<slug>/`，写真实 `archived_at`，更新所有受影响引用。
9. **最终校验**：若 docs-architect 可用，运行 `check -> index --write -> check`；检查 Git diff 只包含预期 close 变化。
10. **Git 边界（按授权）**：若已授权 commit，将 spec merge、文档同步、压缩、时间、移动和索引一起提交；成功后才按授权 push。若 commit 未获授权，保留已校验的 worktree Close，明确报告 `closed in working tree; uncommitted`，不得伪造 commit 或 push。若仓库政策把 commit 规定为 requirement 的完成 gate，则保持 requirement 未完成并报告所缺 authority。

CLI 的 journal、预计算、atomic replace、move 与 rollback 是文件系统完整性边界；**Git commit 是获授权时的 durable/reviewable 边界**。最终检查失败时既不 commit，也不报告成功。没有 commit 时可以准确报告 worktree 已 Close，但不能声称已经形成 repository-level atomic revision。

## 中断恢复与幂等

close 可重入：

1. 搜索 active 和 archive 中相同 REQ ID，不以目录位置推断状态。
2. 读取 verification 的 close attempt、Git status/diff、主 spec 中的 BR/SC ID。
3. 已合并的 delta 不重复追加；按 ID比较预期内容。
4. 已提升的 ADR/docs 不复制；复用其稳定关系。
5. 已删除的临时文件不重建；已移动但未通过最终校验的 archive 继续完成或在安全时恢复 active 路径。
6. 最终校验成功后，文件系统 attempt 可标为 succeeded；Git commit/push 结果单独记录。若 commit 是本 requirement 的明示验收条件，则其完成前 requirement 仍不得标 `done`。

不要用破坏性 reset 清理半完成 close，也不要覆盖用户同期修改。

## 知识压缩

把材料分成三类：

### Promote：进入长期真相

- 合并后的主 product spec；
- 当前架构、运行、配置或用户文档；
- 跨 change 仍有价值的重大决定（ADR）；
- 未解决且仍有效的工作（新 REQ/issue）；
- 有期限的风险接受/waiver。

### Compress：保留简洁历史

默认 summary archive 保留：

- proposal 的意图、范围、验收、真实时间与 status history；
- delta spec 或可明确还原本次行为变化的摘要；
- `verification.md` 中的证据索引、命令结果摘要、review disposition、commit/PR/release 引用；
- change-local 且解释实现所必需的 design 内容；
- tasks 的最终 outcome、关键恢复/迁移信息和实现 commit 映射。

详细逐步日志应压缩成结论，不保留大量空 checkbox 与重复状态表。

### Delete：临时工作材料

- 已解决的逐视角 review 报告和零 finding 报告；
- 重复 research 摘录、候选方案草稿和已吸收的外部资料缓存；
- 调试日志、临时截图、性能试跑和无证据价值的命令输出；
- 重复的进度表、会话 Todo、agent prompt/output；
- 已被 ADR/system docs 完整提升的中间说明。

删除前确保没有 evidence `ref`、链接或未解决 finding 仍指向该文件。

## Retention profiles

| Profile | 何时使用 | 保留范围 |
|---|---|---|
| `summary`（默认） | 普通产品/工程 change | 上述 Promote + Compress；删除显式登记的临时材料 |
| `minimal` | 项目明确只靠 Git/issue 保存历史，且无审计义务 | proposal/completion/evidence 索引与必要链接；其余已提升后删除 |
| `compliance` | 法规、合同、合规或用户明确要求 | 保留完整 evidence pack、review provenance 与审批；仍去重并标状态 |

不能因为 change 很大就自动选择 `compliance`。profile 在 intake/proposal 中确定，close 时复核。summary/minimal 只能删除 proposal metadata `ephemeral_artifacts` 中显式登记且位于 change 内的普通文件；禁止用 glob 猜测临时材料。

## 归档后不变式

- active `changes/` 中不再存在已完成 REQ；
- 主 specs 描述实际交付行为；
- archive ID、时间和索引顺序可由 metadata 验证；
- 没有悬空 evidence/link/relation；
- 没有只存在于已删除 review 文件中的未解决事项；
- 再运行一次 close/check 不产生材料差异。

归档幂等的例外是合法的后续演进：旧 change 再次 Close 时，CLI 会按 `archived_at` 回放
之后已归档、触及同一 `BR-*` 的 MODIFIED/RENAMED/REMOVED delta，并将终态与当前 spec 比较。
稳定 ID 不可通过后续 ADDED 回收；同一时间戳的后继 lineage 视为歧义并阻断。
