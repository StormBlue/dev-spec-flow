# Git 流程：先建分支 · 每任务 commit · 里程碑 push

留痕要细（commit 到单任务粒度），但推远端要稳（push 到里程碑/授权粒度）。这样既能随时回滚到某个任务，又不会把半成品频繁推上共享远端。

---

## 0. 开发前：先建 feature 分支

进入 Phase 3 开发循环**之前**，先切一个 feature 分支，不要直接在 `main`/`master`/`dev` 等共享分支上做：

```bash
git switch -c feat/<change-id>      # 如 feat/add-team-todo
```

分支名跟 change-id 对齐，或跟项目已有约定走（先扫 `git branch -a` 和 `git log` 看习惯）。

---

## 1. 每个任务：commit（本地粒度）

```
任务 T 自检完毕 → 测试通过 → 备注块写完 → tasks.md 状态改 ✅ → commit
```

**单任务一个 commit**，文档改动跟代码一起进这个 commit（见下「文档与代码一起 commit」）。

不要：
- ❌ 攒一堆任务才 commit（回滚粒度太粗）
- ❌ 自检/测试还没过就 commit

---

## 2. 里程碑边界：push

**不必每个任务都 push。** 在里程碑边界（一组关联任务全 ✅、跑完增量验证）统一 push：

```
里程碑 M 全部 ✅ → 跑增量验证（测试 + 真跑 app）→ push
```

```bash
git push -u origin feat/<change-id>   # 首次
git push                              # 之后
```

**什么时候可以更早 push**：用户明确要求、或你长时间在自己的独立分支上工作（怕机器挂丢进度）。**协作仓库 / 共享分支**按团队约定走（通常是开 PR），不要擅自推。

> 一句话：**commit 频（每任务），push 稳（每里程碑或授权时）**。push 是 outward-facing 动作，缺省保守。

---

## 3. Commit 信息约定

**默认走 Conventional Commits**（除非项目已有别的约定，扫一遍 `git log` 跟着学）：

```
<type>(<scope>): <subject>

<body, 可选>
```

| type | 用途 | | type | 用途 |
|------|------|-|------|------|
| `feat` | 新功能 | | `docs` | 文档 |
| `fix` | bug 修复 | | `test` | 测试 |
| `refactor` | 重构（不改行为） | | `chore` | 构建/工具/杂项 |
| `perf` | 性能 | | `ci` | CI/CD |
| `style` | 代码风格 | | `review` | 审核轮修复（本 skill 约定） |

- subject：祈使句、小写起头、不加句号、≤ 72 字符。中文项目用中文 OK：`feat(auth): 实现邮箱+密码登录`。
- scope：模块/子系统名。

### body 关联任务

任务驱动开发的好习惯——commit body 链接 `tasks.md` 中的任务编号：

```
feat(auth): 实现邮箱+密码登录

完成 openspec/changes/user-system/tasks.md 中的 Task 2.1（实现 R-auth-1）。

- 添加 /api/login endpoint
- 用 argon2 哈希密码
- 加 rate limit (5 次/分钟)
- 测试：覆盖 spec 中"凭据有效/无效"两个 scenario
```

---

## 4. 文档与代码一起 commit

每个任务结束时 `tasks.md` 已被改过（状态、备注），可能 `proposal.md`/`spec.md`/`design.md` 也被改过（实现偏离时实时更新）。这些**和代码改动一起 commit**，不要单独拆成 `docs:`：

```bash
git add src/auth.ts openspec/changes/user-system/tasks.md
git commit -m "feat(auth): 实现登录"
```

**例外**：纯文档改动（修文案、补图）走 `docs:` 没问题。归档（Phase 5，merge delta 回 `openspec/specs/`）单独 commit，如 `chore(specs): 归档 add-2fa，merge 进 auth spec`。

---

## 5. 不能做的事

绝不在没有用户明确授权时做：

- `git push --force` / `--force-with-lease`
- `git reset --hard <公共分支>`
- `git rebase -i` / `git commit --amend` 已推过的 commit
- 删远程分支（`git push origin --delete`）
- 跳 hook（`--no-verify`）

**hook 失败时**：① 看错误、理解为什么挂 ② 修根因（lint 报错改代码、test 挂改实现）③ **不要 amend 那个失败的 commit**（hook 失败时 commit 其实没发生），修好后重新 stage + commit。

---

## 6. 完整 commit 示例

```bash
git status   # 先确认 staging 干净、没有 secret 文件
git commit -m "$(cat <<'EOF'
feat(payment): 接入 Stripe Checkout

完成 openspec/changes/payment/tasks.md Task 1.3（实现 R-payment-1、R-payment-2）。

实现要点：
- 用 Stripe Checkout Session（hosted page，避免自己处理 PCI）
- webhook 用 raw body + 签名校验防伪造
- 幂等接收，失败重试交给 Stripe

依赖：stripe@17.4.0（锁死版本）
测试：覆盖 spec 的 3 个 scenario + webhook 重放
EOF
)"
```

里程碑做完再 `git push`。
