# Tauri 2.x 外部 URL 加载 Capability 配置规则（CODING-048）

> 复盘来源：Tauri 2.x 加载本地 SPA 服务（`http://localhost:3000`）时报 `URL: local only`，根因是 capability 中用了顶层 `urls` 字段，Tauri 2.x 要求外部 URL 必须放在 `remote.urls` 子字段。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `tauri_external_url` 字段读取，禁止在规则文件中硬编码端口号或 URL 模式。

## 触发场景

- Tauri 2.x 通过 `WebviewUrl::External(url)` 加载外部 URL（如本地 SPA 服务、远程页面）
- 运行时控制台报 `URL: local only` 或 `URL not allowed`
- Capability 中配置外部 URL 访问权限
- 多环境切换（dev 加载 `localhost:PORT`，prod 加载 `tauri://localhost`）
- Code Review capability 文件时

## 不适用场景

- Tauri 1.x 项目（URL 白名单配置方式不同，用 `tauri.conf.json` 的 `security.csp` 与 `dangerousUseHttpScheme`）
- 仅加载内置资源（`WebviewUrl::App("index.html")`）的纯离线应用
- Electron 的 `webSecurity` / `BrowserWindow.loadURL` 配置

## 规则

**外部 URL 必须配置在 `remote.urls` 子字段，而非顶层 `urls` 字段**。URL 模式支持通配符 `*`，端口必须与实际监听端口一致。

### 为什么

Tauri 2.x 的 ACL 模型将 URL 访问权限分为两层：

- **顶层 `urls`**：仅声明 webview 可以加载的本地资源路径（如 `tauri://localhost`），不接受外部 HTTP/HTTPS URL
- **`remote.urls`**：声明 webview 可以加载的远程 URL 白名单，支持 glob 模式（如 `http://localhost:3000/*`）

误把外部 URL 放在顶层 `urls` 会导致 Tauri runtime 判定为"仅允许本地资源"，外部 URL 加载被拒绝并报 `URL: local only`。

## 判断逻辑

```
配置外部 URL 访问:
  IF URL 是 http:// 或 https:// 协议:
      必须放在 capabilities 文件的 remote.urls 数组
      IF URL 含端口号 → 端口必须与实际监听端口一致（从 tauri_external_url.allowed_url_patterns 匹配）
      IF URL 是动态端口 → 用通配符 http://localhost:PORT/*（仅 dev 环境，prod 必须固定端口）
  ELSE IF URL 是 tauri:// 或内置资源:
      放在顶层 urls 数组
  ELSE:
      禁止加载（非白名单协议）

错误诊断:
  IF 报 'URL: local only' → remote.urls 未配置或 URL 放错位置（在顶层 urls）
  IF 报 'URL not allowed: http://...' → remote.urls 缺少该 URL 模式
  IF 报 'Connection refused' → URL 端口与实际监听端口不一致
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `tauri_external_url.enabled` | `true` | 是否启用外部 URL 配置守卫 |
| `tauri_external_url.severity` | `error` | 违规严重级别 |
| `tauri_external_url.capabilities_file` | `capabilities/default.json` | capability 配置文件路径 |
| `tauri_external_url.required_field` | `remote.urls` | 外部 URL 必须放置的字段（点分隔路径） |
| `tauri_external_url.forbidden_field` | `urls` | 禁止放置外部 URL 的字段（顶层 urls） |
| `tauri_external_url.allowed_url_patterns` | `http://localhost:3000/*, http://127.0.0.1:3000/*` | 允许的外部 URL 模式（逗号分隔，支持通配符） |
| `tauri_external_url.dev_port` | `3000` | 开发环境 SPA 服务端口 |
| `tauri_external_url.prod_url` | `tauri://localhost` | 生产环境内置资源 URL |
| `tauri_external_url.url_pattern_glob` | `true` | URL 模式是否支持 glob 通配符 |
| `tauri_external_url.diagnostic_map.url_local_only` | `remote.urls 未配置或格式错误` | 'URL: local only' 错误诊断说明 |

## 正确示例

### 开发环境加载本地 SPA 服务

```json
// capabilities/default.json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "windows": ["main"],
  "permissions": [
    "core:default"
  ],
  "remote": {
    "urls": [
      "http://localhost:3000/*",
      "http://127.0.0.1:3000/*"
    ]
  }
}
```

```rust
// src/lib.rs - dev 模式加载外部 URL
tauri::Builder::default()
    .setup(|app| {
        let window = app.get_webview_window("main").unwrap();
        // dev 环境加载本地 SPA 服务（端口从 config 读取）
        #[cfg(dev)]
        window.url().set("http://localhost:3000/".parse().unwrap())?;
        Ok(())
    })
    .run(tauri::generate_context!())
```

### 多环境配置（dev / prod 切换）

```rust
// 通过 cfg 区分 dev/prod，避免在 prod 加载未启动的本地服务
const SPA_URL: &str = if cfg!(dev) {
    "http://localhost:3000/"  // dev：加载 Vite dev server
} else {
    "tauri://localhost/"      // prod：加载内置资源
};
```

## 错误示例

### 错误 1：外部 URL 放在顶层 urls

```json
// ❌ 顶层 urls 仅接受本地资源路径，外部 URL 必须放 remote.urls
{
  "identifier": "default",
  "windows": ["main"],
  "urls": [
    "http://localhost:3000/*"
  ]
}
```

### 错误 2：缺少通配符

```json
// ❌ 缺少路径通配符，子路径加载被拒绝
{
  "remote": {
    "urls": [
      "http://localhost:3000"
    ]
  }
}
```

```json
// ✅ 必须包含路径通配符
{
  "remote": {
    "urls": [
      "http://localhost:3000/*"
    ]
  }
}
```

### 错误 3：端口不匹配

```json
// ❌ capabilities 配置 3000 端口，但实际 SPA 服务监听 5173
{
  "remote": {
    "urls": [
      "http://localhost:3000/*"
    ]
  }
}
// 运行时报 Connection refused（3000 端口无服务）
```

## 错误诊断速查表

| 运行时报错 | 根因 | 修复动作 |
|-----------|------|---------|
| `URL: local only` | 外部 URL 放在顶层 `urls`，或 `remote.urls` 未配置 | 将 URL 移至 `remote.urls` 数组 |
| `URL not allowed: http://...` | `remote.urls` 缺少该 URL 模式 | 追加 URL 模式到 `remote.urls`，含路径通配符 |
| `Connection refused` | URL 端口与实际监听端口不一致 | 核对 `dev_port` 与 SPA 服务实际监听端口 |
| `CSP violation` | CSP 头未允许该域 | 在 `tauri.conf.json` 的 `security.csp` 追加域 |

## 适用场景

- Tauri 2.x 加载本地 SPA 服务（Vue/React/Vite dev server）
- Tauri 2.x 加载远程页面（如 OAuth 回调页、第三方集成）
- 多窗口项目中不同窗口加载不同外部 URL
- dev/prod 环境切换 URL 策略

## 适配新项目

- **纯离线 Tauri 应用**：将 `enabled` 设为 `false`，无需配置 `remote.urls`
- **远程 SPA 部署**：`allowed_url_patterns` 改为 `https://your-app.example.com/*`
- **多端口项目**（API + Web 分离）：`allowed_url_patterns` 列出所有端口模式
- **动态端口项目**：dev 环境用 `http://localhost:*/*` 通配，prod 固定端口
- **OAuth 集成**：`remote.urls` 追加 OAuth 提供商回调 URL 模式
