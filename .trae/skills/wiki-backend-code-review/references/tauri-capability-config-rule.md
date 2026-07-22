# Tauri Capability 配置审查规则（BR-041~044）

> 复盘来源：Tauri 2.x 桌面应用集成中，自定义命令未在 `build.rs` 的 `AppManifest::commands` 注册、`capabilities/default.json` 缺失 `allow-xxx` 权限声明、`remote.urls` 配置格式错误（误用顶层 `urls` 而非 `remote: { urls: [] }`）、`tauri.conf.json` 未引用 `default` capability，导致运行时调用自定义命令抛 `command not allowed` 或外部 URL 加载被静默拦截。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"Tauri Capability 配置审查参数（tauri_capability_config）"章节读取，禁止在本规则文件硬编码具体命令名、权限名或 URL 模式。

## Trigger Keywords

build.rs, AppManifest, commands, capabilities/default.json, permissions, allow-, remote, urls, tauri.conf.json, app.security, capabilities, invoke, tauri::generate_handler, tauri::command, capability, ACL

## Rules

### BR-041: `build.rs` 必须显式声明 `AppManifest::commands` 注册所有自定义命令

- **Severity**: critical
- **Description**: Tauri 2.x 引入了 Capability-based ACL 系统，前端通过 `invoke('<command>')` 调用的所有 Rust 自定义命令（用 `#[tauri::command]` 标注的函数）必须在 `build.rs` 的 `tauri_build::try_build()` 配置中通过 `AppManifest::commands()` 显式注册。未注册的命令在运行时会被 ACL 拒绝（前端 `invoke` 抛 `command not allowed`），但编译期不报错——问题仅在运行时暴露。评审时须对比 `src-tauri/src/` 下所有 `#[tauri::command]` 标注的函数名与 `build.rs` 中 `AppManifest::commands(...)` 列表，差异即视为不通过。
- **Suggested fix**:

```rust
// src-tauri/src/commands.rs —— 自定义命令定义
#[tauri::command]
pub async fn load_vault_content(app: AppHandle, path: String) -> Result<String, String> {
    // ...
}

#[tauri::command]
pub async fn save_markdown(path: String, content: String) -> Result<(), String> {
    // ...
}

// src-tauri/src/lib.rs —— invoke_handler 注册
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            load_vault_content,
            save_markdown,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

// src-tauri/build.rs —— AppManifest::commands 显式注册
fn main() {
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .commands([
                "load_vault_content",
                "save_markdown",
            ])
            .into()
    )
    .expect("failed to run tauri-build");
}
```

### BR-042: `capabilities/default.json` 的 `permissions` 数组必须包含所有 `allow-<command>` 权限

- **Severity**: critical
- **Description**: Tauri 2.x 的 Capability 系统要求每个被 `AppManifest::commands` 注册的命令都须在 `capabilities/default.json` 的 `permissions` 数组中显式声明 `allow-<command>` 权限（如 `"allow-load-vault-content"`），否则即使 `build.rs` 注册了命令，前端 `invoke` 仍会被 ACL 拒绝。`permissions` 数组还须包含插件权限（如 `"core:default"` / `"shell:allow-open"` 等内置插件权限）。评审时须对比 `build.rs` 中注册的命令列表与 `capabilities/default.json` 的 `permissions` 中 `allow-` 前缀条目，差异即视为不通过。
- **Suggested fix**:

```json
// src-tauri/capabilities/default.json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "默认 capability，包含应用所有自定义命令与插件权限",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "core:window:allow-close",
    "core:window:allow-minimize",
    "shell:allow-open",
    // 自定义命令权限（每个 build.rs 中注册的命令都须有对应 allow-xxx）
    "allow-load-vault-content",
    "allow-save-markdown"
  ]
}
```

### BR-043: 外部 URL 加载场景必须配置 `remote.urls` 且格式正确

- **Severity**: critical
- **Description**: 当 Tauri WebView 需要加载外部 URL（如远程开发服务器、第三方 OAuth 回调页、CDN 资源）时，必须在 `capabilities/default.json` 的 `permissions` 中添加 `"core:webview:allow-external-urls"` 权限，并在 capability 顶层对象中配置 `remote: { urls: ["<pattern>"] }`（嵌套在 `remote` 对象下，**不是**顶层 `urls` 数组）。常见错误是把 `urls` 写在顶层（`{ "urls": [...] }`），Tauri 解析时会忽略该字段并静默拦截外部 URL 加载，导致 WebView 白屏或 OAuth 回调失败。评审时须确认 `remote.urls` 的格式为嵌套结构，且 URL 模式与实际加载的外部 URL 匹配。
- **Suggested fix**:

```json
// 错误 1：urls 写在顶层（会被 Tauri 忽略，外部 URL 静默被拦截）
{
  "identifier": "default",
  "permissions": ["core:default"],
  "urls": ["https://*.example.com/*"]   // ❌ 顶层 urls 无效
}

// 错误 2：缺少 core:webview:allow-external-urls 权限
{
  "identifier": "default",
  "permissions": ["core:default"],
  "remote": { "urls": ["https://*.example.com/*"] }  // ❌ 缺权限，仍被拦截
}

// 正确：remote.urls 嵌套 + 权限声明齐全
{
  "identifier": "default",
  "permissions": [
    "core:default",
    "core:webview:allow-external-urls"   // ✅ 显式声明外部 URL 权限
  ],
  "remote": {
    "urls": [
      "https://*.example.com/*",
      "http://localhost:*/*"             // ✅ 开发模式本地服务器
    ]
  }
}
```

### BR-044: `tauri.conf.json` 的 `app.security.capabilities` 必须引用 `default`

- **Severity**: critical
- **Description**: `tauri.conf.json` 的 `app.security.capabilities` 数组必须显式引用 `default`（即 capability 文件的 `identifier`），否则即使 `capabilities/default.json` 配置正确，Tauri 运行时也不会加载该 capability，所有 `invoke` 调用都会被 ACL 拒绝。`capabilities` 数组可包含多个 capability identifier（如 `["default", "window-capability"]`），但至少须包含 `"default"`。评审时须确认 `tauri.conf.json` 中 `app.security.capabilities` 字段存在且包含 `"default"`，且与 `capabilities/` 目录下的 `<identifier>.json` 文件名（不含扩展名）一一对应。
- **Suggested fix**:

```json
// src-tauri/tauri.conf.json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "KarpathyWiki",
  "version": "1.0.0",
  "app": {
    "security": {
      // ✅ 显式引用 default capability
      "capabilities": ["default"]
    },
    "windows": [
      {
        "title": "Karpathy AI Wiki",
        "width": 1280,
        "height": 800
      }
    ]
  }
}
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `tauri_capability_config.enabled` | `true` | 是否启用本组规则（BR-041~044） |
| `tauri_capability_config.severity_br041` | `critical` | BR-041 build.rs AppManifest::commands 注册缺失违规严重级别 |
| `tauri_capability_config.severity_br042` | `critical` | BR-042 capabilities/default.json permissions 缺失违规严重级别 |
| `tauri_capability_config.severity_br043` | `critical` | BR-043 remote.urls 格式错误违规严重级别 |
| `tauri_capability_config.severity_br044` | `critical` | BR-044 tauri.conf.json capabilities 引用缺失违规严重级别 |
| `tauri_capability_config.build_rs_path` | `src-tauri/build.rs` | build.rs 文件路径（相对项目根） |
| `tauri_capability_config.command_source_directory` | `src-tauri/src/` | 自定义命令源码目录（用于检索 `#[tauri::command]` 标注的函数） |
| `tauri_capability_config.command_decorator_pattern` | `#\[tauri::command\]` | 自定义命令装饰器匹配模式（正则） |
| `tauri_capability_config.app_manifest_method_pattern` | `AppManifest::commands\|\.commands\(` | AppManifest::commands 调用匹配模式（正则） |
| `tauri_capability_config.capabilities_directory` | `src-tauri/capabilities/` | capability 文件目录（相对项目根） |
| `tauri_capability_config.default_capability_file` | `default.json` | 默认 capability 文件名（在 `capabilities_directory` 下） |
| `tauri_capability_config.default_capability_identifier` | `default` | 默认 capability 的 identifier 值（须被 tauri.conf.json 引用） |
| `tauri_capability_config.permissions_array_field` | `permissions` | capability JSON 中权限数组字段名 |
| `tauri_capability_config.allow_prefix` | `allow-` | 自定义命令权限前缀（如 `allow-load-vault-content`） |
| `tauri_capability_config.required_core_permissions` | `core:default` | 必备的核心插件权限（逗号分隔） |
| `tauri_capability_config.external_url_permission` | `core:webview:allow-external-urls` | 加载外部 URL 所需权限名 |
| `tauri_capability_config.remote_field_name` | `remote` | 外部 URL 配置的嵌套字段名（非顶层 `urls`） |
| `tauri_capability_config.url_patterns_field` | `urls` | `remote` 对象下 URL 列表字段名 |
| `tauri_capability_config.tauri_conf_path` | `src-tauri/tauri.conf.json` | tauri.conf.json 文件路径（相对项目根） |
| `tauri_capability_config.capabilities_reference_path` | `app.security.capabilities` | tauri.conf.json 中 capability 引用的 JSON 路径 |

## 检查方式

1. **BR-041 检查**：
   - 用 Grep 检索 `tauri_capability_config.command_source_directory` 下所有 `.rs` 文件，匹配 `tauri_capability_config.command_decorator_pattern`（如 `#\[tauri::command\]`），提取紧邻的 `pub async fn <name>` 或 `pub fn <name>` 中的函数名。
   - 用 Read 读取 `tauri_capability_config.build_rs_path`，提取 `tauri_capability_config.app_manifest_method_pattern` 调用处的命令名字符串列表。
   - 对比两个列表：源码中定义但 build.rs 未注册 → BR-041 违规。
2. **BR-042 检查**：
   - 用 Read 读取 `tauri_capability_config.capabilities_directory` / `tauri_capability_config.default_capability_file`。
   - 提取 `permissions` 数组中所有 `allow-` 前缀条目（去掉前缀得到命令名）。
   - 对比 BR-041 中 build.rs 注册的命令列表：注册但 permissions 缺失 `allow-<command>` → BR-042 违规。
   - 检查 `permissions` 是否包含 `required_core_permissions` 中的所有项：缺失 → BR-042 违规（建议级）。
3. **BR-043 检查**：
   - 在 capability JSON 中检索顶层 `urls` 字段：
     - 命中 → BR-043 违规（urls 写在顶层，应嵌套在 remote 下）
   - 在 capability JSON 中检索 `remote` 对象：
     - 命中 → 检查 `remote.urls` 是否存在且为数组
     - 未命中但应用有外部 URL 加载场景（如 OAuth / 远程服务器） → BR-043 违规（缺失 remote 配置）
   - 若 `remote.urls` 存在，检查是否包含 `tauri_capability_config.external_url_permission`：
     - 缺失 → BR-043 违规（缺权限声明）
4. **BR-044 检查**：
   - 用 Read 读取 `tauri_capability_config.tauri_conf_path`。
   - 按 `tauri_capability_config.capabilities_reference_path`（如 `app.security.capabilities`）路径访问数组。
   - 检查数组是否包含 `tauri_capability_config.default_capability_identifier`（如 `"default"`）：
     - 缺失 → BR-044 违规
   - 用 Glob 列出 `tauri_capability_config.capabilities_directory` 下所有 `.json` 文件名（不含扩展名），与 capabilities 数组对比：
     - 数组引用了不存在的 capability 文件 → BR-044 违规
     - 存在但未被引用的 capability 文件 → suggestion 级 warning（建议清理或引用）

## 正确示例

```rust
// src-tauri/src/commands.rs —— 自定义命令定义
#[tauri::command]
pub async fn load_vault_content(app: AppHandle, path: String) -> Result<String, String> {
    let content = std::fs::read_to_string(&path).map_err(|e| e.to_string())?;
    Ok(content)
}

#[tauri::command]
pub async fn save_markdown(path: String, content: String) -> Result<(), String> {
    std::fs::write(&path, content).map_err(|e| e.to_string())?;
    Ok(())
}
```

```rust
// src-tauri/build.rs —— AppManifest::commands 显式注册
fn main() {
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .commands([
                "load_vault_content",
                "save_markdown",
            ])
            .into()
    )
    .expect("failed to run tauri-build");
}
```

```rust
// src-tauri/src/lib.rs —— invoke_handler 注册
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            load_vault_content,
            save_markdown,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

```json
// src-tauri/capabilities/default.json —— 权限声明齐全
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "默认 capability",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "core:window:allow-close",
    "core:webview:allow-external-urls",
    "allow-load-vault-content",
    "allow-save-markdown"
  ],
  "remote": {
    "urls": [
      "https://*.example.com/*",
      "http://localhost:*/*"
    ]
  }
}
```

```json
// src-tauri/tauri.conf.json —— capabilities 引用 default
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "KarpathyWiki",
  "version": "1.0.0",
  "app": {
    "security": {
      "capabilities": ["default"]
    }
  }
}
```

## 错误示例

```rust
// 错误 1：build.rs 缺失 AppManifest::commands 注册（BR-041 违规）
// src-tauri/src/commands.rs 中定义了 #[tauri::command] save_markdown
// src-tauri/build.rs
fn main() {
    tauri_build::build()   // ❌ 用 build() 而非 try_build() + commands 注册
}
// 运行时 invoke('save_markdown') → "command not allowed"

// 错误 2：build.rs 注册了命令但 capabilities/default.json 缺权限（BR-042 违规）
// build.rs 中注册了 "save_markdown"
// capabilities/default.json
{
  "identifier": "default",
  "permissions": [
    "core:default",
    "allow-load-vault-content"
    // ❌ 缺 "allow-save-markdown"
  ]
}
// 运行时 invoke('save_markdown') 仍被 ACL 拒绝

// 错误 3：urls 写在顶层（BR-043 违规）
{
  "identifier": "default",
  "permissions": ["core:default", "core:webview:allow-external-urls"],
  "urls": ["https://*.example.com/*"]   // ❌ 顶层 urls 无效，应嵌套在 remote 下
}
// WebView 加载外部 URL 时被静默拦截，无报错日志

// 错误 4：tauri.conf.json 未引用 default（BR-044 违规）
{
  "app": {
    "security": {
      // ❌ 缺 capabilities 字段，或 capabilities: [] 空数组
    }
  }
}
// 所有 invoke 调用都被 ACL 拒绝

// 错误 5：remote 配置存在但缺权限（BR-043 违规）
{
  "identifier": "default",
  "permissions": ["core:default"],
  "remote": { "urls": ["https://*.example.com/*"] }  // ❌ 缺 core:webview:allow-external-urls
}
```

## 适配新项目

- **不同 Tauri 版本项目**：Tauri 1.x 用 `tauri.conf.json` 的 `allowlist` 字段（白名单模式），Tauri 2.x 用 capability-based ACL 系统——本规则仅适用于 Tauri 2.x；Tauri 1.x 项目应将 `enabled` 设为 `false`。
- **多 capability 项目**：若应用按窗口/角色拆分多个 capability 文件（如 `default.json` + `admin.json`），`default_capability_identifier` 仍为 `"default"`，但 `tauri.conf.json` 的 `capabilities` 数组须包含所有 identifier；BR-042 检查须对每个 capability 文件分别校验 permissions 与 build.rs 注册命令的对应关系。
- **插件权限项目**：若应用使用了 Tauri 插件（如 `tauri-plugin-shell` / `tauri-plugin-fs`），`required_core_permissions` 须追加插件权限（如 `shell:allow-open` / `fs:allow-read-text-file`），按项目实际使用的插件扩展。
- **不同 src-tauri 目录结构项目**：若 `src-tauri/` 目录重命名（如 `desktop/`），`build_rs_path` / `capabilities_directory` / `tauri_conf_path` 调整为实际路径，其余规则不变。
- **远程 URL 加载项目**：若应用完全离线（无外部 URL 加载场景），可跳过 BR-043 检查——在 `external_url_permission` 设为空字符串表示禁用本子规则。
