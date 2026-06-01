# 调研策略与工具优先级

Phase 1 的核心问题：**怎么快速搞清楚做这事的最佳实践，不要拍脑门**？

---

## 工具优先级（从高到低）

### 1. context7 MCP（如果可用）

**最适合**：库 / 框架 / SDK / CLI 工具的最新文档。它只有两个工具：

```
resolve-library-id
  → 给 libraryName 拿到 /org/project 形式的 ID
get-library-docs
  → 用上一步的 ID 拿到精准的当前版本文档（可指定 topic）
```

> 实际工具名前缀随安装方式而定（如插件形式可能是 `mcp__plugin_context7_context7__resolve-library-id`），但核心两个动作就是 `resolve-library-id` → `get-library-docs`。**先看自己环境里 context7 是否真的可用**，不可用就走下面的 WebFetch 官方文档。

**为什么优先**：训练数据里的 API 经常已经过时，特别是 React、Next.js、Tailwind、Pydantic 这种迭代快的库。context7 给的是当前最新文档。

**典型场景**：

- "用 Next.js App Router 怎么做 streaming?"
- "Stripe Checkout 现在的 webhook 签名校验怎么写？"
- "TanStack Query v5 的 useQuery 接口"

### 2. 当前可用的相关 skill

**先看自己这个环境里实际加载了哪些 skill**（不同用户/项目装的 skill 不一样，不要假设某个一定存在）。看到有对得上当前任务的，优先用——skill 本身就是该领域最佳实践的集合，比自己从头调研快得多。

常见可能有用的类型（**有才用，没有就跳过**）：

| 任务类型 | 可能的 skill（如环境里存在） |
|----------|------------------------------|
| 前端 / UI 设计 | 前端设计类 skill |
| Anthropic API / Claude SDK | Claude API 类 skill |
| Figma 设计稿实现 / 设计系统 | Figma 集成类 skill |
| 项目文档架构 | 文档架构类 skill |
| 代码简化 / 安全审计 | `/simplify`、`/security-review`（通常内置） |

判断"有没有"的依据是当前会话里 system reminder 列出的 available skills，而不是这张表。

### 3. WebSearch / WebFetch

**最适合**：

- 业界趋势 / 最佳实践 / 设计模式比较
- 找参考项目（GitHub 上的同类 OSS）
- 找设计参考（Dribbble / Mobbin / 真实产品）
- 看博客 / 官方设计文档

**搜索技巧**：

- 加上当前年份限定结果新鲜度（"2026 best practice for X"）
- 加 `site:github.com` 找代码示例
- 找 RFC、design doc、changelog 比新闻报道靠谱

### 4. 阅读项目自身代码

**永远要做**。在调研 "X 怎么实现" 之前，先扫一遍现有项目：

- **`openspec/specs/`**（如有）——这是系统当前行为的真相源，最权威的现状描述，且能告诉你这次改动该落在哪个 domain、是否触及已有 Requirement。
- `README.md`、`ARCHITECTURE.md`、`docs/`
- `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod` 的依赖列表
- 已有的相似模块怎么写的（最大的灵感来源）
- 项目特有的工具函数、helper、abstraction

**为什么**：项目已有的约定 > 业界最佳实践。你的目标是融入这个项目，不是给它另起炉灶。

---

## 调研产出格式

调研做完，给用户一份**技术决策摘要**。模板：

```markdown
# 技术调研：<Feature Name>

## 1. 核心选型

| 维度 | 选型 | 理由 | 备选 |
|------|------|------|------|
| 框架 | Next.js 15 | App Router 适合 SSR，团队已用 | Remix（少一票） |
| 状态 | TanStack Query | 服务端状态最佳实践 | SWR（功能少） |
| ... | ... | ... | ... |

## 2. 关键架构模式

- **模式 A**：用 Server Components 做数据初始拉取，Client Components 做交互
- **模式 B**：API 用 tRPC 统一类型
- ...

## 3. 主要风险

| 风险 | 概率 | 缓解 |
|------|------|------|
| 第三方 SDK 限流 | 中 | 加缓存 + 限速 + 重试 |
| ... | ... | ... |

## 4. 留给用户决策的开放问题

- [ ] 选 Stripe 还是 Paddle？（影响订阅模型）
- [ ] 是否需要支持离线？（影响 PWA / 本地存储设计）
- [ ] 支持的语言列表？

## 5. 参考资料

- [Next.js App Router 官方迁移指南](url)
- [Stripe Checkout best practices](url)
- 类似项目: [openstatus/openstatus](https://github.com/...) — 状态页参考
```

---

## 反模式

❌ **不调研直接写**：靠记忆中的 API 写代码，跑起来才发现接口变了。

❌ **过度调研**：调研一星期还没出方案。**给自己定时间盒** —— 大需求 1-2h，小需求 15-30min。

❌ **调研结果不告诉用户**：自己默默选了一个栈就开干，用户后来才发现选错了。**永远要给用户看摘要**。

❌ **不留参考链接**：决策完没记 source。半年后回看忘了为什么选这个。
