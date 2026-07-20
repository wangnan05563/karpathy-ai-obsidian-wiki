# Rule Catalog - Scroll Container (Frontend Layout)

## Scope
- Covers: 前端布局中滚动容器单一职责、flex 子项自然高度保护、`glass-card` 类组件 `overflow: hidden` 副作用预防。
- Does NOT cover: CSS Grid 布局（grid 子项默认不收缩）、原生块级元素堆叠（无 flex 容器）、SSR 首屏渲染（属于后端/构建范畴）。

> 所有可配置参数（最大嵌套层数、flex-shrink 必备标志、glass-card 选择器等）集中定义在 [config/review-config.md](../config/review-config.md) 的"滚动容器审查参数"段。本文件只描述通用模式，不硬编码具体值。

## Rules

### SC-1: 滚动容器嵌套层数不得超过上限

IsUrgent: True
Category: Scroll Container

### Description

容器链路上 `overflow-y: auto` / `overflow-y: scroll` 的嵌套层数不得超过 `scroll_container.max_overflow_layers`（默认 `1`）。当外层容器（如 `.content`）已设 `overflow-y: auto` 时，内层容器（如 `.help-content-area`）不得再次设置 `overflow-y: auto`，否则会形成双重滚动嵌套。

双重滚动的危害：
- flex 子项默认 `flex: 0 1 auto`，在双重滚动容器中被等比压缩到 `min-content` 高度（约 50px）
- 内容卡片仅显示标题一行，下方 intro/blocks/表格全部不可见
- 标题文字被截断（如"快速开始使用文档"被截断为"快速开始"）

### Judgment Logic

1. 在目标 `.vue` / `.css` 文件中检索 `overflow-y:\s*(auto|scroll)` 出现位置。
2. 沿 DOM 层级链路向上追踪父容器，统计 `overflow-y: auto|scroll` 出现层数。
3. 若嵌套层数 > `scroll_container.max_overflow_layers`（默认 1），告警并指出外层与内层位置。
4. 检查 `flex-direction: column + flex: 1` 容器内的自然高度子项是否设置 `flex-shrink: 0`。

### Applicable Scenarios

- Vue 3 + flex 布局的多卡片长内容页面（帮助文档、设置面板、仪表盘卡片堆叠）。
- 外层已设 `overflow-y: auto` 接管页面滚动的 SPA 应用。
- 全局 `.glass-card` 类（或类似卡片类）有 `overflow: hidden` 副作用的项目。

### Non-Applicable Scenarios

- CSS Grid 布局（grid 子项默认不收缩，无需 flex-shrink 守卫）。
- 原生块级元素堆叠（无 flex 容器，自然撑开高度）。
- 桌面端固定高度窗口（无页面滚动需求）。

### Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `scroll_container.max_overflow_layers` | `1` | 容器链路上 `overflow-y: auto` 最大嵌套层数 |
| `scroll_container.flex_shrink_required_in_flex_column` | `true` | `flex-direction: column + flex: 1` 容器内的自然高度子项必须 `flex-shrink: 0` |
| `scroll_container.glass_card_selectors` | `.glass-card` | 全局可能产生 `overflow: hidden` 副作用的卡片类选择器清单 |
| `scroll_container.outer_scroll_selectors` | `.content, .app-shell` | 已设 `overflow-y: auto` 接管滚动的外层容器选择器清单 |

### Example

```vue
<!-- ❌ Wrong: 双重滚动嵌套 -->
<template>
  <div class="content">  <!-- 外层 .content 已有 overflow-y: auto -->
    <div class="help-content-area">  <!-- 内层又设 overflow-y: auto → 双重滚动 -->
      <div class="glass-card">...</div>  <!-- 卡片被压缩到 ~50px -->
    </div>
  </div>
</template>

<style scoped>
.help-content-area {
  flex: 1;
  overflow-y: auto;  /* ❌ 与外层形成双重滚动 */
}
</style>

<!-- ✅ Right: 单一滚动容器 -->
<template>
  <div class="content">  <!-- 外层 .content 接管滚动 -->
    <div class="help-content-area">  <!-- 内层不再设 overflow -->
      <div class="glass-card">...</div>  <!-- 卡片按内容自然高度撑开 -->
    </div>
  </div>
</template>

<style scoped>
.help-content-area {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  /* ✅ 移除 overflow-y: auto，让外层 .content 统一接管滚动 */
}

.intro-card,
.section-card {
  flex-shrink: 0;  /* ✅ 防止 flex 子项被压缩到 min-content */
}
</style>
```

### Checklist

- [ ] 容器链路上 `overflow-y: auto` 嵌套层数 ≤ `scroll_container.max_overflow_layers`（默认 1）
- [ ] `flex-direction: column + flex: 1` 容器内的自然高度子项已设 `flex-shrink: 0`
- [ ] 全局 `.glass-card` 类（或类似卡片类）的 `overflow: hidden` 已与子内容高度需求对齐
- [ ] 验证卡片实际渲染高度从 `min-content`（~50px）变为内容自然高度（数百 px+）
