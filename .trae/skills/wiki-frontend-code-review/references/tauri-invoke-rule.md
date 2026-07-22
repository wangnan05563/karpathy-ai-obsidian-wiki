# Tauri invoke 命令三层声明审查（FR-041）

> 复盘来源：Tauri 2.x 桌面应用集成中，前端调用 `invoke('start_dragging')` 等命令时，因命令名未在 `build.rs` 的 `AppManifest::commands`、`capabilities/default.json` 的 `permissions` 数组、`lib.rs` 的 `invoke_handler` 三层中任一层缺失声明，导致运行时报 `Plugin not found` 或 `not allowed to execute command xxx` 错误，且因错误发生在桌面运行时（非浏览器 dev server），调试链路长。
> 所有可变参数从 config/review-config.md 的 `tauri_invoke_frontend` 字段读取。

## 规则

### FR-041-1：每个 invoke 命令必须三层声明齐全

前端代码中出现的每一个 `invoke('xxx')` 调用，其命令名 `xxx` 必须在以下三层中同时声明，缺一不可：

| 层级 | 文件位置 | 声明形式 |
|------|---------|---------|
| 第 1 层（构建清单） | `src-tauri/build.rs` | `AppManifest::commands` 数组含 `"xxx"` 字符串 |
| 第 2 层（权限清单） | `src-tauri/capabilities/default.json` | `permissions` 数组含 `"core:default:allow-xxx"` 或自定义权限 `"allow-xxx"` |
| 第 3 层（运行时注册） | `src-tauri/src/lib.rs` | `invoke_handler!()` 宏的 `generate_handler!` 含对应 Rust 函数 `xxx` |

判断标准：三层任一层缺失 → 审查失败（FAIL）。

### FR-041-2：错误诊断关键词对照

运行时错误信息按层级映射，便于快速定位缺失的声明层：

| 错误关键词 | 缺失层级 | 排查文件 |
|-----------|---------|---------|
| `Plugin not found` | 第 1 层（构建清单未声明） | `build.rs` |
| `not allowed to execute command` / `not allowed to ...` | 第 2 层（权限清单未授权） | `capabilities/default.json` |
| `command xxx not found` / `handler not registered` | 第 3 层（运行时未注册） | `lib.rs` |

### FR-041-3：命令名拼写一致性

三层中命令名字符串必须完全一致（区分大小写）。常见错误：

- 前端用驼峰 `startDragging`，Rust 端用 snake_case `start_dragging` —— Tauri 默认会把 invoke 命令名转成 snake_case 匹配，但显式声明层必须对齐。
- 第 2 层 `allow-xxx` 的 `xxx` 必须与第 1 层、第 3 层的命令名同名。

## 适用场景

- Tauri 2.x 桌面应用项目，前端通过 `@tauri-apps/api` 的 `invoke()` 调用 Rust 后端命令。
- 前端代码位于 `frontend/` 或 `src/` 目录，Rust 代码位于 `src-tauri/`。
- 提交前自查（pending-change review）或定向评审涉及 invoke 调用的前端文件。

## 不适用场景

- 纯 Web 项目（无 Tauri 集成）。
- Tauri 1.x 项目（命令注册机制不同，使用 `tauri::generate_handler!` 但无 capabilities 权限层）。
- 仅通过 Tauri 插件提供的现成命令（如 `@tauri-apps/plugin-window` 的 `appWindow.startDragging()`），这些命令的声明由插件自带，无需用户在 build.rs 声明。

## 检查流程

```
[开始] 扫描前端 invoke 调用
  │
  ▼
[1] 提取所有 invoke('xxx') 命令名集合 A
  │
  ▼
[2] 读 build.rs，提取 AppManifest::commands 数组 → 集合 B（第 1 层）
  │
  ▼
[3] 读 capabilities/default.json，提取 permissions 数组 → 集合 C（第 2 层）
  │  └─ 去除 allow- 前缀得到命令名
  │
  ▼
[4] 读 lib.rs，提取 invoke_handler! → generate_handler! 中的函数名 → 集合 D（第 3 层）
  │
  ▼
[5] 对集合 A 中每个命令 x：
  │  ├─ x ∉ B → FAIL（第 1 层缺失，错误关键词 'Plugin not found'）
  │  ├─ x ∉ C → FAIL（第 2 层缺失，错误关键词 'not allowed'）
  │  └─ x ∉ D → FAIL（第 3 层缺失，错误关键词 'command not found'）
  │
  ▼
[6] 全部命中 → PASS
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `tauri_invoke_frontend.build_manifest_path` | `src-tauri/build.rs` | 第 1 层构建清单文件路径（相对项目根） |
| `tauri_invoke_frontend.capabilities_path` | `src-tauri/capabilities/default.json` | 第 2 层权限清单文件路径 |
| `tauri_invoke_frontend.runtime_handler_path` | `src-tauri/src/lib.rs` | 第 3 层运行时注册文件路径 |
| `tauri_invoke_frontend.commands` | `[]` | 项目实际使用的 invoke 命令名清单（逗号分隔）；留空表示从源码自动扫描 |
| `tauri_invoke_frontend.permission_prefix` | `allow-` | 第 2 层权限名前缀，去除后与命令名比对 |
| `tauri_invoke_frontend.error_keyword_layer1` | `Plugin not found` | 第 1 层缺失的运行时错误关键词 |
| `tauri_invoke_frontend.error_keyword_layer2` | `not allowed` | 第 2 层缺失的运行时错误关键词 |
| `tauri_invoke_frontend.error_keyword_layer3` | `command not found` | 第 3 层缺失的运行时错误关键词 |
| `tauri_invoke_frontend.plugin_command_allowlist` | `[]` | 插件自带命令白名单（如 `start_dragging`、`set_title`），不纳入三层检查 |

## 检查方式

1. Grep 前端代码中的 `invoke('xxx')` / `invoke("xxx")` 调用，提取命令名集合。
2. 排除 `plugin_command_allowlist` 中的插件命令（如 `start_dragging` 由 window 插件提供，自带声明）。
3. 读 `build_manifest_path` 文件，在 `AppManifest::commands` 或等价声明位置提取命令名集合。
4. 读 `capabilities_path` JSON 文件，从 `permissions` 数组去除 `permission_prefix` 前缀后得到命令名集合。
5. 读 `runtime_handler_path` 文件，在 `generate_handler!` 宏中提取 Rust 函数名集合。
6. 对照三层集合，输出缺失项 + 对应错误关键词。

## 正确示例

```rust
// ✅ src-tauri/build.rs — 第 1 层：构建清单声明
fn main() {
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .tauri_app_manifest(|manifest| {
                let mut manifest = manifest;
                manifest.commands = vec![
                    "start_dragging".to_string(),   // ← 命令 1
                    "save_config".to_string(),      // ← 命令 2
                    "load_config".to_string(),      // ← 命令 3
                ];
                manifest
            })
            .unwrap(),
    )
    .expect("failed to run tauri-build");
}
```

```json
// ✅ src-tauri/capabilities/default.json — 第 2 层：权限清单声明
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "core:window:allow-start-dragging",     // ← 对应 start_dragging（插件命令可省略）
    "allow-save-config",                    // ← 对应 save_config
    "allow-load-config"                     // ← 对应 load_config
  ]
}
```

```rust
// ✅ src-tauri/src/lib.rs — 第 3 层：运行时注册
#[tauri::command]
fn save_config(app: tauri::AppHandle, payload: ConfigPayload) -> Result<(), String> {
    // ...业务逻辑
    Ok(())
}

#[tauri::command]
fn load_config(app: tauri::AppHandle) -> Result<ConfigPayload, String> {
    // ...业务逻辑
    Ok(payload)
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_window::init())  // 插件命令 start_dragging 由插件注册
        .invoke_handler(tauri::generate_handler![
            save_config,   // ← 注册命令 2
            load_config    // ← 注册命令 3
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

```ts
// ✅ 前端调用
import { invoke } from '@tauri-apps/api/core'

// 自定义命令（须三层齐全）
await invoke('save_config', { payload: config })
const config = await invoke('load_config')

// 插件命令（在 plugin_command_allowlist 中，跳过三层检查）
await invoke('start_dragging')
```

## 错误示例

```ts
// ❌ 前端调用了 'open_folder' 但 build.rs / capabilities / lib.rs 都未声明
import { invoke } from '@tauri-apps/api/core'

async function openFolder(path: string) {
  // 运行时报错：Plugin not found（第 1 层缺失）
  // 或：not allowed to execute command open_folder（第 2 层缺失）
  // 或：command open_folder not found（第 3 层缺失）
  await invoke('open_folder', { path })
}
```

```rust
// ❌ 第 1 层缺失：build.rs 中 AppManifest::commands 漏写 "open_folder"
// 前端调用 invoke('open_folder') → 运行时 'Plugin not found'
```

```json
// ❌ 第 2 层缺失：capabilities/default.json 的 permissions 数组漏写 "allow-open-folder"
// 前端调用 invoke('open_folder') → 运行时 'not allowed to execute command open_folder'
```

```rust
// ❌ 第 3 层缺失：lib.rs 的 generate_handler! 未注册 open_folder 函数
// 前端调用 invoke('open_folder') → 运行时 'command open_folder not found'
```

```ts
// ❌ 命令名大小写不一致：前端 'saveConfig'，Rust 端 'save_config'
// Tauri 默认会做 snake_case 转换，但显式声明层若混用大小写仍可能失配
await invoke('saveConfig', { payload: config })  // ❌ 应统一为 'save_config'
```

## 适配新项目

- **Tauri 2.x 新项目**：调整 `build_manifest_path` / `capabilities_path` / `runtime_handler_path` 为实际路径，把项目用到的所有 invoke 命令名填入 `commands` 或留空让其自动扫描。
- **多 capabilities 文件项目**：若 `capabilities/` 下有多个 JSON 文件（如 `main.json`、`window.json`），需逐个扫描 `permissions` 数组并合并去重。
- **自定义权限命名规范**：若项目不用 `allow-xxx` 前缀（如直接用命令名作为权限名），调整 `permission_prefix` 为空字符串。
- **插件命令扩展**：项目使用其他 Tauri 插件（如 `tauri-plugin-fs`、`tauri-plugin-dialog`）时，把插件提供的命令名加入 `plugin_command_allowlist`，避免误报。

## 输出格式

```
FAIL — invoke 命令 'open_folder' 三层声明缺失
  第 1 层（build.rs AppManifest::commands）：缺失
    排查文件：src-tauri/build.rs
    运行时错误关键词：Plugin not found
  第 2 层（capabilities/default.json permissions）：缺失
    排查文件：src-tauri/capabilities/default.json
    运行时错误关键词：not allowed to execute command open_folder
  第 3 层（lib.rs invoke_handler）：缺失
    排查文件：src-tauri/src/lib.rs
    运行时错误关键词：command open_folder not found

修复建议：
  1. 在 build.rs 的 AppManifest::commands 数组追加 "open_folder"
  2. 在 capabilities/default.json 的 permissions 数组追加 "allow-open-folder"
  3. 在 lib.rs 实现 #[tauri::command] fn open_folder(...) 并加入 generate_handler!
```
