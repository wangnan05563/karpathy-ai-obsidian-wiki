# Tauri 多 Webview 状态隔离规则（CODING-049）

> 复盘来源：Tauri 桌面应用主窗口与悬浮窗口同源（`http://localhost:3000`），通过 `initialization_script` 设置 `localStorage` 作为模式标记，导致两个 webview 的 localStorage 互相污染，悬浮窗口模式标记被主窗口覆盖。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `tauri_webview_isolation` 字段读取，禁止在规则文件中硬编码属性名或阈值。

## 触发场景

- Tauri 2.x 创建多个 webview 窗口（主窗口 + 悬浮窗口 + 设置窗口等）
- 多个 webview 加载同源 URL（同一 SPA 服务）
- 需要为不同 webview 设置独立的模式标记（如 `floating mode` / `main mode`）
- 通过 `initialization_script` 注入启动状态
- 运行时发现 webview 间状态串扰（A 窗口的设置影响 B 窗口）
- Code Review 多窗口代码时

## 不适用场景

- 单窗口 Tauri 应用（无 webview 间隔离需求）
- 不同源 webview（localStorage 天然隔离）
- Electron 的 `BrowserWindow`（每个 window 有独立 session，规则不适用）
- Web 浏览器的多 tab（同源 tab 共享 localStorage 是预期行为）

## 规则

### 规则 1：禁止用 `initialization_script` 设置 `localStorage`

`initialization_script` 在 webview 的 JS context 加载前执行，但同源 webview **共享同一个 localStorage**。通过 `initialization_script` 写 `localStorage` 会导致后启动的 webview 覆盖先启动的 webview 的值，造成状态污染。

### 规则 2：用 `webview.eval()` 设置 `window` 属性

`window` 属性是 per-webview 的 JS context 隔离的，不会跨 webview 共享。通过 `webview.eval("window.__MODE__ = 'floating'")` 注入模式标记，每个 webview 独立持有。

### 规则 3：`WebviewUrl::External` 的 hash 不可靠

`WebviewUrl::External("http://localhost:3000/#floating")` 的 hash 部分在某些 Tauri 版本与 WebView2 实现中会被规范化或丢失，不能作为模式检测信号。必须用 `webview.eval()` 注入 `window` 属性作为可靠的模式检测信号。

### 为什么

- **localStorage 共享性**：同源 webview 共享同一个 localStorage 存储（W3C 标准），A webview 写 `localStorage.mode = 'floating'` 后，B webview 读 `localStorage.mode` 得到 `'floating'`，而非 B 自己的 `'main'`
- **window 属性隔离性**：每个 webview 有独立的 JS context，`window.__MODE__` 仅在当前 webview 可见，天然隔离
- **hash 不可靠性**：WebView2 在某些 URL 规范化场景会丢失 hash，且 hash 变化会触发 `hashchange` 事件干扰 SPA 路由

## 判断逻辑

```
为不同 webview 设置模式标记:
  IF 用 initialization_script 写 localStorage:
      ❌ 禁止（同源 webview 共享 localStorage，会污染）
  ELSE IF 用 WebviewUrl::External 的 hash 区分模式:
      ❌ 禁止（hash 不可靠，可能被规范化丢失）
  ELSE IF 用 webview.eval() 设置 window 属性:
      ✅ 正确（JS context 隔离，每个 webview 独立持有）

多 webview 状态共享策略:
  IF 状态需要跨 webview 共享（如全局主题）:
      用 Tauri 事件系统（emit/listen）同步，而非 localStorage
  ELSE IF 状态仅当前 webview 使用（如模式标记）:
      用 window 属性 + eval() 注入
  ELSE IF 状态需要持久化且跨 webview:
      用 Rust 后端存储 + invoke 命令读取
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `tauri_webview_isolation.enabled` | `true` | 是否启用 webview 隔离守卫 |
| `tauri_webview_isolation.severity` | `error` | 违规严重级别 |
| `tauri_webview_isolation.forbidden_isolation_methods` | `initialization_script+localStorage, external_url_hash` | 禁止的状态隔离方法（逗号分隔） |
| `tauri_webview_isolation.recommended_isolation_method` | `webview.eval + window property` | 推荐的状态隔离方法 |
| `tauri_webview_isolation.window_property_prefix` | `__TAURI_` | window 属性命名前缀（避免与业务变量冲突） |
| `tauri_webview_isolation.cross_webview_sync_method` | `tauri_event_system` | 跨 webview 状态同步方法（emit/listen） |
| `tauri_webview_isolation.shared_storage_forbidden` | `localStorage, sessionStorage` | 同源 webview 共享的存储（禁止用作隔离） |
| `tauri_webview_isolation.eval_timing` | `on_webview_created` | eval() 注入时机（webview 创建后立即执行） |

## 正确示例

### 用 `webview.eval()` 注入模式标记

```rust
// src/lib.rs
use tauri::{WebviewWindow, Manager};

#[tauri::command]
async fn create_floating_window(app: tauri::AppHandle) -> Result<(), String> {
    let floating = WebviewWindow::builder(
        &app,
        "floating",
        WebviewUrl::External("http://localhost:3000/".parse().unwrap()),
    )
    .title("Floating")
    .build()
    .map_err(|e| e.to_string())?;

    // ✅ 用 eval() 设置 window 属性，JS context 隔离
    // window 属性仅当前 webview 可见，不会污染主窗口
    floating.eval("window.__TAURI_MODE__ = 'floating'")
        .map_err(|e| e.to_string())?;

    Ok(())
}

#[tauri::command]
async fn create_main_window(app: tauri::AppHandle) -> Result<(), String> {
    let main = WebviewWindow::builder(
        &app,
        "main",
        WebviewUrl::External("http://localhost:3000/".parse().unwrap()),
    )
    .title("Main")
    .build()
    .map_err(|e| e.to_string())?;

    main.eval("window.__TAURI_MODE__ = 'main'")
        .map_err(|e| e.to_string())?;

    Ok(())
}
```

### 前端读取模式标记

```typescript
// packages/web/src/utils/tauri-mode.ts
// 从 window 属性读取模式，避免 localStorage 污染
export function getTauriMode(): 'main' | 'floating' | 'settings' | null {
  // window 属性由 Rust 端 eval() 注入，仅当前 webview 可见
  const mode = (window as any).__TAURI_MODE__;
  return mode ?? null;
}

export function isFloatingMode(): boolean {
  return getTauriMode() === 'floating';
}
```

### 跨 webview 状态同步用事件系统

```rust
// 跨 webview 同步主题切换（不用 localStorage）
#[tauri::command]
async fn sync_theme(theme: String, app: tauri::AppHandle) -> Result<(), String> {
    // 通过事件系统广播，所有 webview 监听
    app.emit("theme-changed", &theme)
        .map_err(|e| e.to_string())?;
    Ok(())
}
```

```typescript
// 各 webview 监听主题事件
import { listen } from '@tauri-apps/api/event';

listen('theme-changed', (event) => {
  applyTheme(event.payload as string);
});
```

## 错误示例

### 错误 1：用 `initialization_script` 写 `localStorage`

```rust
// ❌ 同源 webview 共享 localStorage，后启动的会覆盖先启动的
let floating = WebviewWindow::builder(&app, "floating", url)
    .initialization_script("localStorage.setItem('mode', 'floating');")
    .build()?;

let main = WebviewWindow::builder(&app, "main", url)
    .initialization_script("localStorage.setItem('mode', 'main');")  // 覆盖 floating 的值
    .build()?;
// 两个 webview 读 localStorage.getItem('mode') 都得到 'main'
```

### 错误 2：用 URL hash 区分模式

```rust
// ❌ hash 在某些 WebView2 实现中会被规范化丢失
let floating = WebviewWindow::builder(
    &app,
    "floating",
    WebviewUrl::External("http://localhost:3000/#floating".parse().unwrap()),
).build()?;
// 前端读 window.location.hash 可能得到空字符串
```

### 错误 3：用 `sessionStorage` 隔离

```rust
// ❌ sessionStorage 在同源 webview 间行为不一致（部分实现共享）
.initialization_script("sessionStorage.setItem('mode', 'floating');")
```

## 错误诊断速查表

| 现象 | 根因 | 修复动作 |
|------|------|---------|
| 多 webview 模式标记互相覆盖 | 用 `localStorage` 隔离同源 webview 状态 | 改用 `webview.eval()` 设置 `window` 属性 |
| 前端读 `window.location.hash` 为空 | `WebviewUrl::External` 的 hash 被规范化 | 改用 `eval()` 注入 `window` 属性 |
| 主窗口主题切换后悬浮窗口未同步 | 用 `localStorage` 跨 webview 同步（不可靠） | 改用 Tauri 事件系统 `emit`/`listen` |
| 悬浮窗口读 `window.__MODE__` 为 `undefined` | `eval()` 在页面 JS 加载前执行 | 在 `setup` 钩子中等待 webview ready 后再 `eval` |

## 适用场景

- Tauri 2.x 多窗口项目（主窗口 + 悬浮窗口 + 设置窗口）
- 同源多 webview 需要独立模式标记
- 跨 webview 状态同步（主题、语言、用户会话）
- dev 环境加载同一 SPA 服务的多窗口

## 适配新项目

- **单窗口项目**：将 `enabled` 设为 `false`，无隔离需求
- **不同源多窗口**：天然 localStorage 隔离，但跨源通信需用 Tauri 事件系统
- **Electron 项目**：每个 `BrowserWindow` 独立 session，规则不适用
- **多窗口共享大量状态**：用 Rust 后端作为状态权威源，各 webview 通过 `invoke` 读取
- **WebView2 / WKWebView 原生项目**：规则同样适用（同源 webview 共享 localStorage 是 W3C 标准）
