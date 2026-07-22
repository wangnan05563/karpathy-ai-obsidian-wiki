# Tauri 透明窗口 CSS 全覆盖规则（CODING-050）

> 复盘来源：Tauri 桌面应用启用 `transparent: true` 实现悬浮窗毛玻璃效果，但仅设置了 `body` 的 `background: transparent`，未覆盖 `html` 与 `#app` 容器，导致悬浮窗边缘出现白色背景方块，毛玻璃效果失效。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `tauri_transparent_window` 字段读取，禁止在规则文件中硬编码 CSS 选择器或 class 名。

## 触发场景

- Tauri 2.x 启用 `transparent: true` 创建透明窗口（悬浮窗、毛玻璃效果、圆角窗口）
- 透明窗口加载 SPA 后出现白色背景方块
- 毛玻璃 / backdrop-filter 效果失效
- 切换 `floating-active` 类后窗口背景未跟随透明
- Code Review 透明窗口相关 CSS 时

## 不适用场景

- 不透明窗口（`transparent: false`，背景色可任意设置）
- Electron 的 `vibrancy` 效果（CSS 规则不同）
- Web 页面的透明效果（无容器层级问题）
- 移动端 App 的透明 Activity（原生渲染，非 CSS）

## 规则

**`transparent(true)` 时必须覆盖 `html` + `body` + `#app` + 所有容器元素的 `background`**，仅设置单一元素的 `background: transparent` 会导致其子元素或父元素的默认背景色透出。

### 为什么

Tauri 的 `transparent: true` 仅让原生窗口本身透明，但 WebView2 / WKWebView 加载的 HTML 文档树中：

- `html` 元素默认 `background-color: transparent`，但部分浏览器渲染时会给 `html` 添加白色背景
- `body` 元素默认 `background-color: white`（用户代理样式表）
- `#app` 等 Vue/React 挂载容器通常继承 `body` 的白色背景
- 任意中间容器（`.layout` / `.wrapper`）若显式设置 `background: white`，会遮挡透明效果

因此必须用 `:global(html.floating-active)` 等选择器显式覆盖所有层级的 `background`，确保从原生窗口到最内层元素的整条渲染链路都透明。

## 判断逻辑

```
启用 transparent(true) 的窗口:
  STEP 1: 在入口 CSS 文件中定义 floating-active 类的透明覆盖规则
  STEP 2: 覆盖层级链路（从外到内）:
      html.floating-active → body → #app → 所有容器 *
  STEP 3: 用 !important 强制覆盖用户代理默认样式（body 的 white 背景）
  STEP 4: Rust 端切换窗口模式时同步 toggle html 的 floating-active 类

CSS 覆盖完整性检查:
  IF 仅设置 body 透明:
      ❌ html 与 #app 的默认背景仍会透出白色
  IF 仅设置 #app 透明:
      ❌ body 的 white 背景会从 #app 边缘透出
  IF 未用 !important:
      ❌ 用户代理样式表的 body { background: white } 优先级可能更高
  IF 未覆盖动态添加的容器:
      ❌ 后续新增的 .layout / .wrapper 容器可能携带白色背景
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `tauri_transparent_window.enabled` | `true` | 是否启用透明窗口 CSS 守卫 |
| `tauri_transparent_window.severity` | `error` | 违规严重级别 |
| `tauri_transparent_window.transparent_class` | `floating-active` | 透明模式激活时 html 元素的 class 名 |
| `tauri_transparent_window.required_selectors` | `html, body, #app, *` | 必须覆盖 background 的选择器列表（逗号分隔） |
| `tauri_transparent_window.required_property` | `background-color` | 必须设置的 CSS 属性 |
| `tauri_transparent_window.required_value` | `transparent` | 必须设置的 CSS 值 |
| `tauri_transparent_window.important_required` | `true` | 是否必须用 `!important` 强制覆盖 |
| `tauri_transparent_window.app_container_id` | `app` | SPA 挂载容器 id（Vue/React 的 `#app`） |
| `tauri_transparent_window.toggle_method` | `eval+classList.toggle` | 切换透明模式的 JS 方法 |
| `tauri_transparent_window.global_selector_prefix` | `:global()` | Svelte/Vue scoped CSS 的全局选择器前缀 |

## 正确示例

### CSS 全覆盖（Vue SFC `<style>` 或全局 CSS）

```css
/* packages/web/src/styles/transparent-window.css */

/* 透明窗口模式：必须覆盖 html → body → #app → 所有容器 *
 * 每一层都必须显式 transparent !important，否则该层默认背景会透出
 * :global() 用于 Vue scoped CSS 突破作用域限制 */
:global(html.floating-active),
:global(html.floating-active body),
:global(html.floating-active #app),
:global(html.floating-active *) {
  background-color: transparent !important;
}

/* 毛玻璃效果容器（仅最内层内容区设置 backdrop-filter） */
:global(html.floating-active .glass-panel) {
  background-color: rgba(255, 255, 255, 0.1) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}
```

### Rust 端切换透明模式

```rust
// src/lib.rs
use tauri::{WebviewWindow, Manager};

#[tauri::command]
async fn enable_floating_mode(window: WebviewWindow) -> Result<(), String> {
    // 通过 eval() 在 html 元素上 toggle floating-active 类
    // CSS 选择器匹配后自动应用透明背景
    window.eval(
        "document.documentElement.classList.add('floating-active');"
    ).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn disable_floating_mode(window: WebviewWindow) -> Result<(), String> {
    window.eval(
        "document.documentElement.classList.remove('floating-active');"
    ).map_err(|e| e.to_string())?;
    Ok(())
}
```

### Tauri 配置启用透明窗口

```json
// tauri.conf.json
{
  "app": {
    "windows": [
      {
        "label": "floating",
        "transparent": true,
        "decorations": false,
        "url": "http://localhost:3000/"
      }
    ]
  }
}
```

## 错误示例

### 错误 1：仅设置 body 透明

```css
/* ❌ html 与 #app 的默认背景仍会透出白色 */
body {
  background-color: transparent !important;
}
```

### 错误 2：未用 `!important`

```css
/* ❌ 用户代理样式表 body { background: white } 优先级可能更高 */
html.floating-active body {
  background-color: transparent;
}
```

### 错误 3：未用 `:global()` 突破 scoped CSS

```css
/* ❌ Vue scoped CSS 中选择器会被加 hash 属性，无法匹配 html 元素 */
html.floating-active body {
  background-color: transparent !important;
}
```

```css
/* ✅ 用 :global() 突破 scoped CSS 限制 */
:global(html.floating-active body) {
  background-color: transparent !important;
}
```

### 错误 4：遗漏动态容器

```css
/* ❌ 仅覆盖 #app，但 .layout-container 仍带白色背景 */
:global(html.floating-active html),
:global(html.floating-active body),
:global(html.floating-active #app) {
  background-color: transparent !important;
}
/* .layout-container 仍显示白色背景 */
```

```css
/* ✅ 用 * 覆盖所有容器 */
:global(html.floating-active *) {
  background-color: transparent !important;
}
/* 然后单独为毛玻璃容器设置半透明背景 */
```

## 错误诊断速查表

| 现象 | 根因 | 修复动作 |
|------|------|---------|
| 透明窗口边缘出现白色方块 | 未覆盖 `html` 或 `body` 的默认背景 | 在 `required_selectors` 列表追加缺失选择器 |
| 毛玻璃效果失效（无模糊） | 中间容器设置 `background: white` 遮挡 | 用 `*` 通配符覆盖所有容器 |
| `floating-active` 类切换无效 | scoped CSS 未用 `:global()` | 选择器外包 `:global()` |
| 切换类后部分元素仍不透明 | 未用 `!important`，被用户代理样式覆盖 | 所有覆盖规则加 `!important` |
| `backdrop-filter` 不生效 | 父元素 `background: transparent` 但子元素有背景 | 仅最内层毛玻璃容器设半透明背景 |

## 适用场景

- Tauri 2.x 透明窗口（悬浮窗、毛玻璃、圆角）
- macOS NSVisualEffectView 毛玻璃效果集成
- Windows Mica / Acrylic 效果集成
- 多模式窗口（普通模式 + 透明悬浮模式切换）
- Vue/React scoped CSS 项目的透明窗口实现

## 适配新项目

- **不透明窗口项目**：将 `enabled` 设为 `false`，无需透明覆盖
- **React 项目**：`app_container_id` 改为 `root`（React 默认挂载点）
- **Svelte 项目**：`global_selector_prefix` 保持 `:global()`（Svelte 原生支持）
- **原生 CSS 项目**（无 scoped）：`global_selector_prefix` 设为空字符串
- **多透明模式项目**：`transparent_class` 列表扩展（如 `floating-active` / `acrylic-active` / `mica-active`）
- **Electron 项目**：规则不适用，Electron 用 `vibrancy` 选项 + `backgroundColor: '#00000000'`
