# Tauri 2.x 自定义命令 ACL 三层声明规则（CODING-047）

> 复盘来源：Tauri 2.x 桌面集成中新增 `invoke` 命令后，运行时报 `Plugin not found` / `not allowed`，根因是 Tauri 2.x 引入了 ACL（Access Control List）权限模型，命令声明需在三层文件同步。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `tauri_acl` 字段读取，禁止在规则文件中硬编码命令名或路径。

## 触发场景

- 在 Tauri 2.x 项目新增 `#[tauri::command]` 修饰的 Rust 函数
- 前端通过 `@tauri-apps/api/core` 的 `invoke('cmd_name', ...)` 调用后端命令
- 运行时出现 `Plugin not found` / `not allowed` / `command X not found` 错误
- Code Review Tauri 桥接代码时
- 升级 Tauri 1.x → 2.x 时核对存量命令的 ACL 完整性

## 不适用场景

- Tauri 1.x 项目（无 ACL 模型，只需 `invoke_handler` 注册）
- 不通过 `invoke` 暴露给前端的纯 Rust 内部函数
- Electron / Wails / Neutralinojs 等其他桌面框架

## 规则

**任何新增 `invoke` 命令必须同步在三层文件中声明**，缺任意一层将导致运行时调用失败：

| 层级 | 文件（从 config 读取） | 声明形式 |
|------|----------------------|---------|
| 第 1 层：构建清单 | `tauri_acl.build_manifest_file`（默认 `build.rs`） | `tauri_build::build_attributes!` 中 `AppManifest::commands(&["cmd_name"])` 显式列出命令名 |
| 第 2 层：权限清单 | `tauri_acl.capabilities_file`（默认 `capabilities/default.json`） | `permissions` 数组含 `"core:default"` + `"allow-cmd-name"`（命名规则：`allow-` + kebab-case 命令名） |
| 第 3 层：处理器注册 | `tauri_acl.handler_registration_file`（默认 `src/lib.rs`） | `tauri::generate_handler![cmd_fn]` 列出函数名 |

### 为什么需要三层

Tauri 2.x 用 ACL 模型替代了 1.x 的"前端可调用所有 invoke_handler 命令"的隐式信任：

- **第 1 层（build.rs）**：构建期生成命令清单元数据，Tauri runtime 据此识别命令存在
- **第 2 层（capabilities）**：声明哪些 window/webview 拥有该命令的调用权限（ capability = window + permissions 集合）
- **第 3 层（lib.rs）**：运行时将命令名映射到具体函数指针

漏掉第 1 层 → 命令在 runtime 元数据中不存在 → `Plugin not found`
漏掉第 2 层 → 命令存在但当前 webview 无权限 → `not allowed`
漏掉第 3 层 → 命令元数据存在但无实现 → `command X not found`

## 判断逻辑

```
新增 invoke 命令 cmd_name:
  STEP 1: 在 build.rs 的 AppManifest::commands 数组追加 "cmd_name"
  STEP 2: 在 capabilities/default.json 的 permissions 数组追加 "allow-cmd-name"
  STEP 3: 在 lib.rs 的 generate_handler! 宏追加 cmd_fn 函数引用
  STEP 4: cargo build 验证编译通过
  STEP 5: 前端 invoke('cmd_name') 验证运行时可调用

错误诊断:
  IF 报 'Plugin not found' → 第 1 层缺失（build.rs 未声明）
  IF 报 'not allowed' 或 'permission denied' → 第 2 层缺失（capabilities 未授权）
  IF 报 'command X not found' → 第 3 层缺失（generate_handler 未注册）
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `tauri_acl.enabled` | `true` | 是否启用 ACL 三层守卫 |
| `tauri_acl.severity` | `error` | 违规严重级别 |
| `tauri_acl.build_manifest_file` | `build.rs` | 第 1 层：构建清单文件 |
| `tauri_acl.capabilities_file` | `capabilities/default.json` | 第 2 层：权限清单文件 |
| `tauri_acl.handler_registration_file` | `src/lib.rs` | 第 3 层：处理器注册文件 |
| `tauri_acl.permission_prefix` | `allow-` | 权限名前缀（拼接命令名） |
| `tauri_acl.command_name_case` | `kebab-case` | 命令名命名风格（与 permission 拼接时使用） |
| `tauri_acl.diagnostic_map.plugin_not_found_layer` | `1` | 'Plugin not found' 对应缺失层级 |
| `tauri_acl.diagnostic_map.not_allowed_layer` | `2` | 'not allowed' 对应缺失层级 |
| `tauri_acl.diagnostic_map.command_not_found_layer` | `3` | 'command X not found' 对应缺失层级 |

## 正确示例

### 第 1 层：build.rs

```rust
// build.rs
fn main() {
    // Tauri 2.x 必须显式声明所有 invoke 命令名，构建期生成 ACL 元数据
    tauri_build::build_attributes! {
        tauri_build::AppManifest {
            commands: &["greet", "save_vault", "read_config"],
            ..Default::default()
        }
    }
    tauri_build::try_build();
}
```

### 第 2 层：capabilities/default.json

```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "主窗口的权限集",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "allow-greet",
    "allow-save-vault",
    "allow-read-config"
  ]
}
```

### 第 3 层：src/lib.rs

```rust
// src/lib.rs
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}!", name)
}

#[tauri::command]
fn save_vault(path: String, content: String) -> Result<(), String> {
    // ...
    Ok(())
}

pub fn run() {
    tauri::Builder::default()
        // 第 3 层：将命令名映射到函数指针
        .invoke_handler(tauri::generate_handler![greet, save_vault, read_config])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

## 错误诊断速查表

| 运行时报错 | 缺失层级 | 修复动作 |
|-----------|---------|---------|
| `Plugin not found: 'cmd_name'` | 第 1 层 | 在 `build.rs` 的 `AppManifest::commands` 数组追加 `"cmd_name"` |
| `not allowed to call cmd_name` / `permission denied` | 第 2 层 | 在 `capabilities/default.json` 的 `permissions` 数组追加 `"allow-cmd-name"` |
| `command cmd_name not found` | 第 3 层 | 在 `lib.rs` 的 `generate_handler!` 宏追加 `cmd_fn` 函数引用 |

## 适用场景

- Tauri 2.x 项目新增任意 `invoke` 命令
- 重命名现有命令（三层同步改名）
- 删除命令（三层同步删除，避免遗留死权限）
- Code Review 时按三层清单逐项核对

## 适配新项目

- **多窗口项目**：为每个窗口创建独立 capability 文件（`capabilities/floating.json` 等），命令权限按窗口需求分配
- **插件化项目**：插件自带 capability，主项目通过 `permissions` 数组引用插件权限（如 `plugin:my-plugin:allow-foo`）
- **Tauri 1.x 升级**：升级时必须为所有存量 `invoke_handler` 命令补齐第 1 层与第 2 层声明
- **移动端项目**（Tauri Mobile）：规则同样适用，capabilities 文件区分 `android` / `iOS` 目标
