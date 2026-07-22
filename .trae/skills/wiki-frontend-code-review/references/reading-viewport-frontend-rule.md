# 阅读视野优化与输入区固定（FR-032）

> 复盘来源：Query.vue / Reader.vue 等阅读类视图在长内容滚动时出现两类问题：（1）标题头（含导航/工具栏）占据视口 30%+ 高度，实际内容区被压缩到 < 60%，长文阅读需频繁滚动；（2）输入区（input-bar）未固定，跟随内容滚动到视口外，用户需要回滚到顶部才能继续输入，体验断裂。
> 所有可变参数从 config/review-config.md 的 `reading_viewport_frontend` 字段读取。

## 规则

### FR-032-1：阅读类视口的版面占比约束

阅读类视图（Query.vue / Reader.vue 等，由 `reading_viewport_frontend.target_views` 指定）在桌面端视口下，下列区域的垂直占比必须满足：

1. **标题头区**（含 logo、标题、工具栏、tab 切换）占比 ≤ `reading_viewport_frontend.header_max_ratio`（默认 `0.15`，即 15%）。
2. **内容阅读区**占比 ≥ `reading_viewport_frontend.content_min_ratio`（默认 `0.75`，即 75%）。
3. **输入区**占比无强制上限，但不得侵占内容区下限（输入区高度变化不应导致内容区低于下限）。

占比以视口高度（`100vh`）为基准计算。响应式断点 `reading_viewport_frontend.responsive_breakpoint` 之下（如移动端 `<768px`）放宽约束，允许标题头占比 ≤ 0.20、内容区 ≥ 0.65（在 config 的 `reading_viewport_frontend.mobile_*` 字段配置）。

### FR-032-2：输入区必须 sticky bottom + 毛玻璃 + z-index

输入区（input-bar）必须满足以下样式约束，以保证长内容滚动时输入区始终可见：

1. **位置**：`position: sticky; bottom: 0;`（或 `position: fixed` + 计算偏移，但 sticky 优先）。
2. **背景**：毛玻璃效果，`backdrop-filter: blur(<blur_radius>)` + 半透明背景色（`background: rgba(<r>, <g>, <b>, <alpha>)`，alpha 值取自 `reading_viewport_frontend.input_bar_alpha`）。
3. **层级**：`z-index` ≥ `reading_viewport_frontend.input_bar_min_zindex`（默认 `2`）。
4. **边框**：顶部细边框（`border-top: 1px solid <border_color>`），与内容区分隔，避免毛玻璃下内容透出干扰阅读。

### FR-032-3：禁止把输入区放进滚动容器内

输入区不得作为内容滚动容器（`overflow-y: auto`）的子元素，否则 sticky 在某些浏览器中失效。正确做法是把输入区作为滚动容器的同级兄弟元素，或放在外层 flex 容器中。

## 适用场景

- Vue 3 阅读类视图：Query.vue、Reader.vue、Help.vue、ChatView.vue 等含大量文本内容 + 底部输入区的页面。
- 桌面端为主、移动端有响应式适配的 SPA。
- 毛玻璃卡片样式（`backdrop-filter`）项目。

## 不适用场景

- 全屏沉浸式视图（如视频播放器、画板），无标题头与输入区分离需求。
- 移动端原生 App（非 Web）。
- 列表/表格类管理后台（输入区为顶部筛选栏，非底部输入）—— 此场景输入区应 sticky top，规则自动失效。

## 检查流程

```
[开始] 评审目标为 reading_viewport_frontend.target_views 中的视图
  │
  ▼
[1] 计算标题头区高度 / 视口高度
  │  └─ > header_max_ratio → 标记 Urgent（FR-032-1）
  │
  ▼
[2] 计算内容阅读区高度 / 视口高度
  │  └─ < content_min_ratio → 标记 Urgent（FR-032-1）
  │
  ▼
[3] 检查输入区 position + bottom
  │  └─ 非 sticky/fixed bottom → 标记 Urgent（FR-032-2）
  │
  ▼
[4] 检查输入区 backdrop-filter + 半透明背景
  │  └─ 缺失 → 标记 Urgent（FR-032-2）
  │
  ▼
[5] 检查输入区 z-index
  │  └─ < input_bar_min_zindex → 标记 Urgent（FR-032-2）
  │
  ▼
[6] 检查输入区是否在滚动容器内
  │  └─ 是 → 标记 Urgent（FR-032-3）
  │
  ▼
[7] 移动端断点下放宽阈值复核
  │  └─ 仍超阈值 → 标记 Urgent（FR-032-1）
  │
  ▼
[结束]
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `reading_viewport_frontend.target_views` | `Query.vue, Reader.vue, Help.vue, ChatView.vue` | 适用本规则的视图文件名清单（逗号分隔） |
| `reading_viewport_frontend.header_max_ratio` | `0.15` | 标题头区垂直占比上限（占视口高度比例） |
| `reading_viewport_frontend.content_min_ratio` | `0.75` | 内容阅读区垂直占比下限 |
| `reading_viewport_frontend.responsive_breakpoint` | `768` | 响应式断点（px），断点下用 mobile_* 阈值 |
| `reading_viewport_frontend.mobile_header_max_ratio` | `0.20` | 移动端标题头占比上限 |
| `reading_viewport_frontend.mobile_content_min_ratio` | `0.65` | 移动端内容区占比下限 |
| `reading_viewport_frontend.input_bar_position` | `sticky` | 输入区定位方式（sticky / fixed） |
| `reading_viewport_frontend.input_bar_bottom` | `0` | 输入区 bottom 偏移（px） |
| `reading_viewport_frontend.input_bar_blur_radius` | `12px` | 毛玻璃模糊半径 |
| `reading_viewport_frontend.input_bar_alpha` | `0.85` | 输入区背景色 alpha 值（0-1） |
| `reading_viewport_frontend.input_bar_min_zindex` | `2` | 输入区最小 z-index |
| `reading_viewport_frontend.input_bar_border_top` | `1px solid rgba(0,0,0,0.08)` | 输入区顶部分隔边框 |
| `reading_viewport_frontend.input_bar_outside_scroll` | `true` | 输入区必须在滚动容器外 |

## 检查方式

1. 在 `target_views` 列表中匹配当前评审的 `.vue` 文件，命中即启用本规则。
2. 用浏览器 DevTools 或 Playwright 测量各区域高度：`document.querySelector(<header_selector>).offsetHeight / window.innerHeight`。
3. 比对标题头比例与 `header_max_ratio`，超阈值即标记 Urgent。
4. 比对内容区比例与 `content_min_ratio`，低于阈值即标记 Urgent。
5. 在源码 `<style>` 中检索输入区选择器（默认 `input-bar` 类，由 `target_views` 推断）的 `position` / `bottom` / `backdrop-filter` / `background` / `z-index` / `border-top` 属性，缺失或不达标即标记。
6. 检查输入区在 DOM 树中是否为 `overflow-y: auto` 容器的直接或间接子节点，是即标记 Urgent。
7. 响应式断点下重复步骤 2-4，阈值替换为 `mobile_*` 版本。

## 正确示例

```vue
<!-- ✅ Query.vue — 标题头 ≤15% + 内容区 ≥75% + 输入区 sticky bottom -->
<template>
  <div class="query-view">
    <!-- 标题头区：高度约 12% 视口 -->
    <header class="query-header">
      <h1>知识查询</h1>
      <nav class="tools">...</nav>
    </header>

    <!-- 内容阅读区：高度约 80% 视口，独立滚动 -->
    <main class="query-content">
      <article v-for="r in results" :key="r.id">{{ r.text }}</article>
    </main>

    <!-- 输入区：sticky bottom + 毛玻璃，与内容区同级（不在滚动容器内） -->
    <footer class="input-bar">
      <input v-model="q" placeholder="输入查询..." />
      <button @click="submit">发送</button>
    </footer>
  </div>
</template>

<style scoped>
.query-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.query-header {
  flex: 0 0 auto;
  /* 高度由内容撑开，约 12vh，≤ header_max_ratio(0.15) */
}

.query-content {
  flex: 1 1 auto;
  overflow-y: auto;
  /* 内容区 ≥ content_min_ratio(0.75) */
}

.input-bar {
  position: sticky;            /* ✅ sticky bottom */
  bottom: 0;                   /* ✅ 贴底 */
  z-index: 2;                  /* ✅ z-index ≥ input_bar_min_zindex */
  backdrop-filter: blur(12px);  /* ✅ 毛玻璃 */
  background: rgba(255, 255, 255, 0.85);  /* ✅ 半透明背景，alpha=0.85 */
  border-top: 1px solid rgba(0, 0, 0, 0.08);  /* ✅ 顶部分隔边框 */
  padding: 12px 16px;
}

@media (max-width: 768px) {
  .query-header { max-height: 20vh; }   /* ✅ 移动端放宽至 mobile_header_max_ratio */
  .query-content { min-height: 65vh; }  /* ✅ 移动端放宽至 mobile_content_min_ratio */
}
</style>
```

## 错误示例

```vue
<!-- ❌ 标题头占比过大 + 输入区未固定 -->
<template>
  <div class="query-view">
    <header class="query-header">
      <h1>知识查询</h1>
      <div class="hero-banner">  <!-- ❌ 大 banner 占用 30vh -->
        <img src="..." />
      </div>
      <nav class="tools">...</nav>
    </header>
    <!-- 标题头占比 ~35%，违反 header_max_ratio(0.15) -->

    <main class="query-content">
      <article v-for="r in results" :key="r.id">{{ r.text }}</article>
      <!-- 内容区仅 ~55vh，低于 content_min_ratio(0.75) -->

      <!-- ❌ 输入区放在滚动容器内 -->
      <footer class="input-bar">
        <input v-model="q" />
      </footer>
    </main>
  </div>
</template>

<style scoped>
.query-header { flex: 0 0 35vh; }  /* ❌ 占比过大 */
.query-content { flex: 1 1 auto; overflow-y: auto; }

.input-bar {
  /* ❌ 缺失 position: sticky / bottom / backdrop-filter / z-index */
  padding: 12px;
  background: #fff;  /* ❌ 不透明背景，无毛玻璃效果 */
}
</style>
```

```vue
<!-- ❌ 输入区 z-index 不足，被内容卡片遮挡 -->
<style scoped>
.input-bar {
  position: sticky;
  bottom: 0;
  z-index: 1;          /* ❌ < input_bar_min_zindex(2)，被 z-index: 1 的内容卡片遮挡 */
  background: rgba(255,255,255,0.85);
  /* ❌ 缺失 backdrop-filter，毛玻璃不生效 */
}
</style>
```

## 适配新项目

- **React / Next.js**：本规则完全适用；样式可用 Tailwind 类（`sticky bottom-0 backdrop-blur-md bg-white/85 z-2`）实现，参数仍从 config 读取。
- **Vue 2**：本规则适用；`<style scoped>` 行为一致，flex 布局兼容性需 IE 11+（项目应已弃用 IE）。
- **纯 JavaScript（无框架）**：本规则降级为 CSS 审查，参数仍从 config 读取；可通过 PostCSS 插件自动化检查占比。
- **移动端优先项目**：`responsive_breakpoint` 调整为更大值（如 `1024`），或反过来把移动端阈值作为默认，桌面端阈值作为放宽版。
- **SSR 项目（Nuxt / Next.js）**：需注意 `position: sticky` 在 SSR 首屏 hydration 前的兼容性，但样式约束本身不变。
