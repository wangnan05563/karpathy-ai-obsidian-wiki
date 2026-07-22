# 透明窗口 CSS 覆盖审查（FR-042）

> 复盘来源：Tauri 2.x 桌面应用启用 `transparent: true` 透明窗口后，前端仅给 `body` 设置 `background: transparent`，但 `html`、`#app` 与中间容器仍保留默认白底，导致桌面窗口四周边缘出现白色光晕；切换到 floating-active 状态时局部容器又残留背景色，破坏悬浮卡片的透明视觉。
> 所有可变参数从 config/review-config.md 的 `tauri_transparent_css_frontend` 字段读取。

## 规则

### FR-042-1：透明窗口项目必须四层背景全覆盖

启用 `transparent(true)` 的 Tauri 窗口，前端必须对以下四层选择器同时设置 `background-color: transparent`（或等价的 `background: transparent`）：

| 层级 | 选择器 | 必需样式 |
|------|--------|---------|
| 第 1 层 | `html` | `background-color: transparent` |
| 第 2 层 | `body` | `background-color: transparent` |
| 第 3 层 | `#app`（或项目入口根选择器，由 config 配置） | `background-color: transparent` |
| 第 4 层 | `*`（所有元素）或在 floating-active 状态下用 `:global(html.floating-active *)` | `background-color: transparent !important` |

判断标准：四层任一层缺失 → 审查失败（FAIL）。

### FR-042-2：floating-active 状态切换须配合通配符覆盖

仅覆盖 `body` 不足以解决窗口激活/失活时的背景残留。当窗口处于 `floating-active` class 作用范围时，必须用如下通配符规则强制覆盖所有后代元素：

```css
:global(html.floating-active *) {
  background-color: transparent !important;
}
```

要点：
- 必须用 `:global()` 包裹（Vue SFC scoped 样式场景），否则作用域哈希会让选择器失配。
- 必须用 `!important`，覆盖 Element Plus 等组件库注入的内联背景。
- `floating-active` class 名通过 config 管理，允许自定义。

### FR-042-3：禁止用 opacity 替代 transparent

`opacity: 0` 会让元素及子元素全部不可见（含文字、交互元素），不能用于实现窗口透明。同理 `visibility: hidden` 也不可。透明背景必须用 `background-color: transparent` 或 `rgba(R, G, B, 0)`，保留文字与交互可读性。

### FR-042-4：毛玻璃卡片仍须显式背景

透明窗口下的毛玻璃卡片（`.glass-card` 或等价类）须显式声明半透明背景（如 `rgba(255, 255, 255, 0.65)`），否则会被通配符规则误清成完全透明，导致内容区无背景层、文字直接叠加在桌面壁纸上可读性差。

判断标准：通配符规则命中后，毛玻璃卡片必须存在显式 `background-color` / `background` 声明覆盖透明，否则告警（WARN）。

## 适用场景

- Tauri 2.x 桌面应用，`tauri.conf.json` 中 `app.windows[].transparent` 设为 `true`。
- 前端含悬浮卡片（floating card）/ 浮动面板布局，须根据窗口激活状态切换透明效果。
- Vue 3 + `<script setup>` + scoped 样式项目（须用 `:global()` 突破作用域）。

## 不适用场景

- 普通非透明窗口项目（`transparent: false` 或未设置）。
- Electron / PWA 项目（窗口透明机制不同）。
- 全屏独占模式应用（无窗口边框概念）。

## 检查流程

```
[开始] 读取 tauri.conf.json
  │
  ▼
[1] 是否启用 transparent: true？
  │  └─ 否 → 不适用本规则，PASS（跳过）
  │
  ▼ 是
[2] 扫描前端 CSS / .vue <style> 块
  │  ├─ 检查 html 选择器是否有 background-color: transparent（第 1 层）
  │  ├─ 检查 body 选择器是否有 background-color: transparent（第 2 层）
  │  ├─ 检查 #app / 入口根选择器是否有 background-color: transparent（第 3 层）
  │  └─ 检查是否有 :global(html.floating-active *) 通配符规则（第 4 层）
  │       └─ 任一层缺失 → FAIL
  │
  ▼
[3] 扫描 opacity / visibility 替代用法
  │  └─ 命中 opacity: 0 或 visibility: hidden 用于窗口透明 → FAIL
  │
  ▼
[4] 毛玻璃卡片显式背景检查
  │  └─ .glass-card 或等价类无显式 background-color → WARN
  │
  ▼
[5] 全部通过 → PASS
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `tauri_transparent_css_frontend.tauri_conf_path` | `src-tauri/tauri.conf.json` | Tauri 配置文件路径，用于读取 `transparent` 字段 |
| `tauri_transparent_css_frontend.floating_active_class` | `floating-active` | 窗口激活态 class 名（挂到 html 元素上） |
| `tauri_transparent_css_frontend.app_root_selector` | `#app` | 前端入口根选择器（Vue 默认 `#app`） |
| `tauri_transparent_css_frontend.required_transparent_layers` | `html, body, #app, *` | 必须设置透明背景的四层选择器（逗号分隔） |
| `tauri_transparent_css_frontend.glass_card_selectors` | `.glass-card` | 毛玻璃卡片选择器清单（逗号分隔），须显式背景 |
| `tauri_transparent_css_frontend.glass_card_min_alpha` | `0.3` | 毛玻璃卡片背景色最小 alpha 值（低于此值可读性差，告警） |
| `tauri_transparent_css_frontend.forbidden_transparent_properties` | `opacity: 0, visibility: hidden` | 禁止用作窗口透明替代的属性（逗号分隔） |
| `tauri_transparent_css_frontend.require_global_wrapper` | `true` | scoped 样式场景是否要求 `:global()` 包裹通配符规则 |

## 检查方式

1. 读 `tauri_conf_path`，确认 `app.windows` 数组中任一窗口 `transparent: true`，否则跳过本规则。
2. 扫描 `frontend/src/style.css` / `frontend/src/App.vue` 的 `<style>` 块 / 全局样式文件，按 `required_transparent_layers` 逐层核对 `background-color` / `background` 是否为 `transparent` 或 `rgba(*, *, *, 0)`。
3. 检查 `:global(html.{floating_active_class} *)` 规则是否存在且带 `!important`。
4. 扫描 `opacity: 0` / `visibility: hidden` 是否被误用于窗口透明场景。
5. 对 `glass_card_selectors` 中每个选择器，检查是否有显式 `background-color` / `background` 声明且 alpha ≥ `glass_card_min_alpha`。

## 正确示例

```css
/* ✅ frontend/src/style.css — 四层全覆盖 */
html,
body,
#app {
  background-color: transparent;
  margin: 0;
  padding: 0;
}

/* ✅ floating-active 状态下用通配符 + !important 覆盖所有元素 */
:global(html.floating-active *) {
  background-color: transparent !important;
}

/* ✅ 毛玻璃卡片显式声明半透明背景 */
.glass-card {
  background-color: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

/* ✅ 文字层显式设置颜色，不被通配符清空 */
.glass-card .title {
  color: #1f2937;
}
```

```vue
<!-- ✅ App.vue 用 scoped 样式时仍用 :global() 突破作用域 -->
<script setup lang="ts">
// ...
</script>

<template>
  <div class="app-shell">
    <FloatingCard />
  </div>
</template>

<style scoped>
/* scoped 样式只作用于本组件元素，须用 :global() 覆盖全局选择器 */
:global(html.floating-active *) {
  background-color: transparent !important;
}

.app-shell {
  /* 局部容器显式声明背景，不被通配符误清 */
  background-color: transparent;
}
</style>
```

## 错误示例

```css
/* ❌ 仅覆盖 body，html/#app 仍为默认白底 */
body {
  background-color: transparent;
}
/* 缺失 html / #app / 通配符规则 → 窗口边缘出现白边 */
```

```css
/* ❌ 用 opacity: 0 实现窗口透明，导致文字与子元素全部不可见 */
#app {
  opacity: 0;
}
```

```css
/* ❌ scoped 样式中未用 :global() 包裹通配符规则，作用域哈希让选择器失配 */
<style scoped>
html.floating-active * {
  background-color: transparent !important;
}
</style>
/* Vue 编译后变成 html.floating-active *[data-v-xxx]，永远匹配不到 */
```

```css
/* ❌ 通配符规则漏写 !important，被 Element Plus 的内联背景覆盖 */
:global(html.floating-active *) {
  background-color: transparent;
}
```

```css
/* ❌ 毛玻璃卡片无显式背景，被通配符清成全透明，文字直接叠在壁纸上 */
.glass-card {
  backdrop-filter: blur(12px);
  /* 缺失 background-color / background → WARN */
}
```

```css
/* ❌ 毛玻璃卡片背景 alpha 过低，文字可读性差 */
.glass-card {
  background-color: rgba(255, 255, 255, 0.1);  /* alpha 0.1 < 0.3 → WARN */
  backdrop-filter: blur(12px);
}
```

## 适配新项目

- **React / Next.js 项目**：CSS 仍走全局样式文件即可，无需 `:global()` 包裹（无 scoped 编译）；若用 CSS Modules 仍需 `:global()`。
- **Tailwind CSS 项目**：用 `bg-transparent` 类替代 `background-color: transparent`，但通配符规则仍需自定义 CSS 一段。
- **非悬浮卡片项目**：若项目无 floating-active 状态切换（窗口始终激活），把 `floating_active_class` 留空，规则降级为只检查四层背景覆盖。
- **多窗口项目**：若不同窗口有不同透明策略（如主窗口透明、设置窗口不透明），按窗口分别检查，须在 config 中分窗口配置 `tauri_conf_path` 与 `required_transparent_layers`。

## 输出格式

```
FAIL — 透明窗口 CSS 覆盖缺失
  tauri.conf.json: app.windows[0].transparent = true
  第 1 层 html 选择器：缺失 background-color: transparent
    排查文件：frontend/src/style.css
  第 2 层 body 选择器：已覆盖 ✅
  第 3 层 #app 选择器：缺失 background-color: transparent
    排查文件：frontend/src/style.css
  第 4 层 :global(html.floating-active *) 通配符规则：缺失
    排查文件：frontend/src/App.vue

修复建议：
  1. 在 frontend/src/style.css 追加：
     html, body, #app {
       background-color: transparent;
     }
  2. 在 frontend/src/App.vue 的 <style scoped> 中追加：
     :global(html.floating-active *) {
       background-color: transparent !important;
     }
```

```
WARN — 毛玻璃卡片缺少显式背景
  .glass-card 选择器无 background-color 声明
  在 floating-active 通配符规则下会被清成全透明，文字可读性差
  排查文件：frontend/src/components/FloatingCard.vue

修复建议：
  .glass-card {
    background-color: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(12px);
  }
```
