# Git 协作与交付

Git 行为首先服从用户明确要求和仓库既有流程。本 skill 提供安全默认值，不擅自覆盖团队的分支、commit、PR 或发布政策。

## 分支

1. 检查当前分支、upstream、工作树和仓库说明。
2. 用户指定在 `develop`、现有 feature 分支或 worktree 中工作时按其要求执行。
3. 用户未指定且共享主分支不适合直接开发时，默认创建符合项目命名的 feature 分支；否则保持当前分支。
4. 不因为模板规则切换分支并遗留用户未提交改动；有冲突风险时先报告。

分支是协作工具，不是 action gate。change ID 与 branch 名可以关联，但稳定身份是 REQ ID，不依赖分支路径。

## Commit 粒度

一个 commit 应是可理解、可评审、可恢复的连贯单元：

- 可以完成一个 task，也可以包含多个不可合理拆分的紧耦合 task；
- 一个大 task 也可以拆成多个保持构建/迁移安全的 commit；
- 代码、对应 delta/tasks/evidence 更新通常同 commit；
- close 的 spec merge、文档同步、压缩、归档和索引在获得 commit 授权时形成一个原子 commit；未获授权时保留经过校验的 worktree Close，并明确标记未提交，不伪造 repository-level 原子 revision。

不强制“每 task 一个 commit”，也不把每次状态 emoji 更新单独 commit。避免把无关重构、格式化或用户已有改动混入。

## Commit 信息与追溯

跟随仓库已有格式；没有约定时可用 Conventional Commits。需要追溯时在 body/trailer 引用稳定 ID：

```text
feat(auth): expire idle sessions

Requirement: REQ-2026-042
Tasks: T-003
Validates: REQ-2026-042#AC-2, SC-auth-012
```

只写实际完成和实际运行结果，不复制整份 tasks 或预测测试状态。

## Push 与远程动作

- push、开 PR、合并、发布和删远程分支是对外动作，按用户请求或仓库自动化执行。
- 用户明确要求推送目标分支时，完成验证与 commit 后推送该分支并核对 remote ref。
- 不把“里程碑完成”当成普遍 push 规则。
- push 被拒绝时先 fetch/检查分歧；不要未经授权 force push 或改写已共享历史。

## 安全边界

未经明确授权不要：

- `push --force`/`--force-with-lease`；
- 对用户或共享历史执行 destructive reset、checkout/restore 覆盖；
- rebase/amend 已推送的公共 commit；
- 删除远程分支、绕过 hooks、提交 secret；
- 用自动 stash/clean 隐藏或删除来源不明的工作树变化。

hook/CI 失败时修根因并重新验证。若失败暴露与当前 change 无关的既有问题，记录证据和影响，不擅自扩大修改范围。

## Close 的 Git 边界

[close-and-retention.md](close-and-retention.md) 的最终 Git commit 是获授权时的逻辑原子边界；文件系统 journal/rollback 是无 commit 情况下的完整性边界。commit 前检查：

- delta 已按 ID 正确 merge；
- active change 已移出且链接/索引有效；
- `completed_at/archived_at` 是真实事件时间；
- 没有遗留临时 review/research/debug 文件；
- staged diff 不含用户无关改动。
