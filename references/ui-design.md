# UI 工作规则

UI 工作优先保持产品一致性和真实可用性。是否需要外部调研与用户确认取决于设计未知和影响面，不是所有 UI 修改的固定前置阶段。

## 先判断路径

### 直接沿用项目模式

适用于文案、局部样式、已有组件的清晰扩展或设计稿精确实现：

1. 读取现有 design tokens、组件库、相似页面和局部规则。
2. 按当前交互与视觉语言实现。
3. 用与改动匹配的 viewport、状态和 a11y evidence 验证。

### 先 explore / 确认方案

以下情况先做有边界的设计探索：

- 新页面/新核心流程，没有现有模式；
- 信息架构、交互方式或视觉方向有多种实质选项；
- 用户给了品牌、竞品、Figma 或具体设计目标；
- 改动会显著改变既有 workflow；
- UX/accessibility 风险高，提前原型比直接编码更便宜。

只有需要用户做产品/设计选择时才暂停确认。可逆的局部布局决策按项目模式推进。

## 项目内调研

检查：

- UI framework、组件库、tokens、字体、icon 与状态组件；
- 相似列表/表单/详情/导航流程；
- 响应式断点、dark mode、i18n、a11y 约定；
- 已有 screenshot/visual/browser 测试；
- 最接近目标目录的设计规则。

优先复用既有组件和交互，不为一个 feature 建第二套 design system。

## 外部参考

当前环境有浏览器、设计 skill、Figma 或图像工具且确实能降低未知时才使用。优先真实同类产品、平台 HIG/design system 和框架官方示例。提炼信息层级、状态与交互原则，不逐像素复制品牌作品。

探索结论写入 design/proposal；原始截图收藏与竞品摘录默认临时，除非它们是批准设计的正式输入。

## 实现完整性

按功能实际需要覆盖：

- loading、empty、error、success、disabled、permission 等状态；
- keyboard、focus、语义标签、读屏名称、对比度和 reduced motion；
- 项目支持的 mobile/tablet/desktop 断点与输入方式；
- 长文本、本地化、缩放与动态内容不溢出/遮挡；
- 暗色模式仅在项目支持时保持一致；
- 操作反馈、错误恢复和 destructive action 的清晰性。

不要为不相关的局部改动扩张成全站 redesign。

## UI Evidence

根据 AC/SC 与风险选择：

- component/existing automated tests：稳定交互契约；
- browser/runtime：核心 flow、键盘与状态切换；
- screenshot：布局、viewport、视觉状态；
- inspection：小型 token/文案/DOM 语义改动；
- a11y tool + manual keyboard/screen-reader check：高风险或核心流程。

记录 viewport、route/state、输入和观察结果。只截默认页面不能证明错误态、响应式或交互完成。证据统一进入 `verification.md`，不额外生成 UI review 堆栈。
