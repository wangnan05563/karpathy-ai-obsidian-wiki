# invoke 权限三层验证流程

> 本文档提供 Tauri 2.x 桌面应用 `invoke` 调用的权限验证方法，覆盖 capabilities.json 声明、permissions 数组、remote.urls 匹配三个层级。
> 所有参数从 `config.yaml` 的 `invoke` 节读取，不在代码中硬编码命令名、权限名或 URL 模式。

## 1. 验证目标

Tauri 2.x 的权限模型与 1.x 不同，前端 `@tauri-apps/api` 的 `invoke` 调用必须在 `capabilities/*.json` 中显式声明权限，否则运行时会报错。本验证流程确保：

- 全部 invoke 命令对应的插件已在 `Cargo.toml` 中声明依赖
- 全部命令权限已在 `capabilities/*.json` 的 `permissions` 数组中显式 allow
- 若启用远程 URL（如 `http://localhost:*`），`remote.urls` 已配置匹配模式

## 2. Tauri 2.x 权限模型简介

Tauri 2.x 的权限模型由三层组成：

```
插件依赖（Cargo.toml）  →  命令权限（capabilities/*.json）  →  远程 URL 白名单（remote.urls）
        ↓                          ↓                                  ↓
   第 1 层验证                  第 2 层验证                          第 3 层验证
```

### 2.1 第 1 层：插件依赖声明

**位置**：`src-tauri/Cargo.toml`

**示例**：
```toml
[dependencies]
tauri = { version = "2", features = [] }
tauri-plugin-log = "2"
tauri-plugin-http = "2"
```

**验证内容**：
- `invoke.commands` 中配置的每个命令，其对应的插件必须在 `Cargo.toml` 的 `[dependencies]` 中声明
- 命令名格式为 `plugin:{plugin_name}|{command_name}`（如 `plugin:log|info`）
- 从命令名提取 `plugin_name`（如 `log`），检查 `Cargo.toml` 是否含 `tauri-plugin-{plugin_name}` 依赖

### 2.2 第 2 层：命令权限声明

**位置**：`src-tauri/capabilities/*.json`（默认 `default.json`）

**示例**：
```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "log:default",
    "allow-log-info",
    "allow-log-warn",
    "allow-log-error",
    "http:default",
    "allow-http-fetch"
  ]
}
```

**验证内容**：
- `invoke.permissions` 中配置的每个权限名，必须在某个 `capabilities/*.json` 的 `permissions` 数组中出现
- 权限名格式为 `allow-{plugin}-{command}`（如 `allow-log-info`、`allow-http-fetch`）

### 2.3 第 3 层：远程 URL 白名单

**位置**：`src-tauri/capabilities/*.json` 的 `remote.urls` 字段

**示例**：
```json
{
  "identifier": "default",
  "permissions": [
    "http:default",
    "allow-http-fetch"
  ],
  "remote": {
    "urls": [
      "http://localhost:*",
      "http://127.0.0.1:*"
    ]
  }
}
```

**验证内容**：
- 若 `invoke.url_patterns` 非空，检查 `remote.urls` 是否包含匹配的模式
- 模式匹配支持 `*` 通配符（如 `http://localhost:*` 匹配 `http://localhost:3000`）
- 验证测试环境使用的 URL（如 `http://localhost:3000/health`）能被 `remote.urls` 中的某个模式匹配

---

## 3. 验证流程

### 3.1 第 1 层验证：插件依赖检查

**输入**：
- `invoke.commands`：命令名列表（如 `["plugin:log|info", "plugin:http|fetch"]`）
- `tauri.src_tauri_dir`：src-tauri 目录路径

**步骤**：
1. 读取 `{tauri.src_tauri_dir}/Cargo.toml`
2. 解析 `[dependencies]` 节
3. 对 `invoke.commands` 中的每个命令：
   - 提取 `plugin_name`（命令名 `:` 后、`|` 前的部分，如 `plugin:log|info` → `log`）
   - 检查 `Cargo.toml` 是否含 `tauri-plugin-{plugin_name}` 依赖
4. 收集缺失的插件依赖列表

**通过条件**：全部命令对应的插件依赖都已声明。

**失败输出示例**：
```
[invoke-L1] Checking plugin dependencies in Cargo.toml...
[invoke-L1]   command "plugin:log|info" → plugin "log" → DEP FOUND (tauri-plugin-log = "2")
[invoke-L1]   command "plugin:http|fetch" → plugin "http" → DEP FOUND (tauri-plugin-http = "2")
[invoke-L1]   command "plugin:shell|execute" → plugin "shell" → DEP MISSING
[invoke-L1] VERDICT: FAIL (1 plugin dependency missing)
[invoke-L1] SUGGESTION: Add "tauri-plugin-shell = \"2\"" to Cargo.toml [dependencies] and run cargo build
```

### 3.2 第 2 层验证：命令权限声明检查

**输入**：
- `invoke.permissions`：权限名列表（如 `["allow-log-info", "allow-http-fetch"]`）
- `tauri.src_tauri_dir`：src-tauri 目录路径

**步骤**：
1. 用 Glob 枚举 `{tauri.src_tauri_dir}/capabilities/*.json` 文件
2. 解析每个 JSON 文件，提取 `permissions` 数组
3. 对 `invoke.permissions` 中的每个权限名：
   - 检查是否在任一 capabilities 文件的 `permissions` 数组中出现
4. 收集缺失的权限声明列表

**通过条件**：全部期望的权限名都已声明。

**失败输出示例**：
```
[invoke-L2] Checking permissions in capabilities/*.json...
[invoke-L2]   Scanning: src-tauri/capabilities/default.json
[invoke-L2]   Scanning: src-tauri/capabilities/main.json
[invoke-L2]   permission "allow-log-info" → FOUND in default.json
[invoke-L2]   permission "allow-http-fetch" → FOUND in default.json
[invoke-L2]   permission "allow-shell-execute" → NOT FOUND
[invoke-L2] VERDICT: FAIL (1 permission not declared)
[invoke-L2] SUGGESTION: Add "allow-shell-execute" to permissions array in src-tauri/capabilities/default.json
```

### 3.3 第 3 层验证：远程 URL 白名单检查

**输入**：
- `invoke.url_patterns`：期望匹配的 URL 模式列表（如 `["http://localhost:*"]`）
- `tauri.src_tauri_dir`：src-tauri 目录路径

**步骤**：
1. 用 Glob 枚举 `{tauri.src_tauri_dir}/capabilities/*.json` 文件
2. 解析每个 JSON 文件，提取 `remote.urls` 数组（若存在）
3. 对 `invoke.url_patterns` 中的每个模式：
   - 检查是否在任一 capabilities 文件的 `remote.urls` 中出现（精确匹配）
   - 或检查 `remote.urls` 中是否有更宽松的模式能覆盖（如 `http://localhost:*` 覆盖 `http://localhost:3000`）
4. 收集未匹配的 URL 模式列表

**通过条件**：
- `invoke.url_patterns` 为空 → 跳过第 3 层验证（默认通过）
- `invoke.url_patterns` 非空 → 全部模式都已被 `remote.urls` 覆盖

**失败输出示例**：
```
[invoke-L3] Checking remote.urls in capabilities/*.json...
[invoke-L3]   Scanning: src-tauri/capabilities/default.json
[invoke-L3]   pattern "http://localhost:*" → MATCHED by remote.urls[0] in default.json
[invoke-L3]   pattern "https://api.example.com/*" → NOT MATCHED
[invoke-L3] VERDICT: FAIL (1 URL pattern not matched)
[invoke-L3] SUGGESTION: Add "https://api.example.com/*" to remote.urls in src-tauri/capabilities/default.json
```

---

## 4. 错误诊断关键词映射

当 Tauri 运行时 invoke 调用失败时，错误消息中的关键词可直接定位到失败的层级：

| 错误消息关键词 | 失败层级 | 失败类型 | 修复建议 |
|----------------|----------|----------|----------|
| `Plugin not found` | 第 1 层 | `invoke_layer_1` | 在 `Cargo.toml` 添加 `tauri-plugin-{plugin_name}` 依赖，运行 `cargo build` |
| `not allowed` | 第 2 层 | `invoke_layer_2` | 在 `capabilities/*.json` 的 `permissions` 数组中添加 `allow-{plugin}-{command}` |
| `URL: local` | 第 3 层 | `invoke_layer_3` | 在 `capabilities/*.json` 的 `remote.urls` 中添加测试 URL 模式 |
| `command not found` | 命令注册 | `command_not_registered` | 在 `lib.rs` 的 `invoke_handler` 中用 `generate_handler![command_name]` 注册命令 |
| `serialization error` | 类型不匹配 | `serde_mismatch` | 检查 Rust 命令参数类型（`serde::Deserialize`）与前端 `invoke` 调用参数是否一致 |
| `expected string, found number` | 类型不匹配 | `serde_type_error` | 前端 `invoke` 传参类型与 Rust 命令签名不符，检查 `invoke(name, args)` 的 `args` 字段类型 |

### 4.1 关键词匹配优先级

当错误消息同时含多个关键词时，按以下优先级匹配（首个命中即停止）：

1. `Plugin not found` → 第 1 层
2. `command not found` → 命令注册
3. `not allowed` → 第 2 层
4. `URL: local` → 第 3 层
5. `serialization error` / `expected string, found number` → 类型不匹配

### 4.2 关键词配置驱动

错误关键词列表从 `config.yaml` 的 `console_log.error_keywords` 读取，不在代码中硬编码：

```yaml
console_log:
  error_keywords:
    - "Plugin not found"
    - "not allowed"
    - "URL: local"
    - "command not found"
    - "serialization error"
    - "panicked at"
```

---

## 5. 配置驱动原则

所有参数从 `config.yaml` 的 `invoke` 节读取，不在代码中硬编码：

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `invoke.commands` | `[]` | 需验证的命令名列表（格式 `plugin:{name}\|{command}`） |
| `invoke.permissions` | `[]` | 期望在 capabilities.json 中见到的权限名列表 |
| `invoke.url_patterns` | `[]` | 远程 URL 模式列表（为空时跳过第 3 层验证） |
| `invoke.capabilities_glob` | `"capabilities/*.json"` | capabilities 文件 glob 模式 |
| `invoke.cargo_toml_path` | `"Cargo.toml"` | Cargo.toml 相对路径（相对 `tauri.src_tauri_dir`） |

**配置示例**：
```yaml
invoke:
  commands:
    - "plugin:log|info"
    - "plugin:log|warn"
    - "plugin:log|error"
    - "plugin:http|fetch"
  permissions:
    - "allow-log-info"
    - "allow-log-warn"
    - "allow-log-error"
    - "allow-http-fetch"
  url_patterns:
    - "http://localhost:*"
    - "http://127.0.0.1:*"
  capabilities_glob: "capabilities/*.json"
  cargo_toml_path: "Cargo.toml"
```

---

## 6. 与 Tauri 测试流程的集成

本验证流程在 Tauri 桌面测试流程中的位置：

```
阶段 3：功能验证
  ├── 3.1 窗口创建验证
  ├── 3.2 invoke 权限验证  ← 本文档（三层验证）
  └── 3.3 交互功能验证

阶段 4：错误诊断
  ├── 4.1 stderr 日志采集
  ├── 4.2 Console 日志采集
  └── 4.3 invoke 错误分类  ← 本文档（关键词映射）
```

- 三层验证（6.1-6.3）在阶段 3.2 执行，作为静态预检
- 关键词映射（第 4 节）在阶段 4.3 执行，作为运行时错误诊断
- 阶段 3.2 的静态预检可提前发现权限缺失，避免阶段 3.3 交互测试时的运行时失败

---

## 7. Python 实现示例

以下代码展示三层验证的核心逻辑，实际实现见 `templates/phase_tauri_desktop.py`：

```python
import os
import json
import glob
import re

def verify_invoke_permissions(cfg, results):
    """invoke 权限三层验证。

    所有命令名、权限名、URL 模式从 config.invoke 读取，
    不在代码中硬编码具体业务命令。
    """
    invoke_cfg = cfg.get("invoke", {})
    tauri_cfg = cfg.get("tauri", {})
    src_tauri_dir = tauri_cfg.get("src_tauri_dir", "src-tauri")
    commands = invoke_cfg.get("commands", [])
    permissions = invoke_cfg.get("permissions", [])
    url_patterns = invoke_cfg.get("url_patterns", [])
    capabilities_glob = invoke_cfg.get("capabilities_glob", "capabilities/*.json")
    cargo_toml_path = invoke_cfg.get("cargo_toml_path", "Cargo.toml")

    # 第 1 层：插件依赖检查
    layer1_pass = True
    cargo_toml_full = os.path.join(src_tauri_dir, cargo_toml_path)
    with open(cargo_toml_full, "r", encoding="utf-8") as f:
        cargo_content = f.read()
    for cmd in commands:
        # 提取插件名：plugin:log|info → log
        match = re.match(r"plugin:([^|]+)\|", cmd)
        if not match:
            continue
        plugin_name = match.group(1)
        dep_name = f"tauri-plugin-{plugin_name}"
        if dep_name not in cargo_content:
            layer1_pass = False
    results.log("invoke-L1-PluginDeps", layer1_pass, "Plugin dependencies check")

    # 第 2 层：命令权限声明检查
    layer2_pass = True
    cap_files = glob.glob(os.path.join(src_tauri_dir, capabilities_glob))
    all_declared_perms = set()
    for cap_file in cap_files:
        with open(cap_file, "r", encoding="utf-8") as f:
            cap_data = json.load(f)
        all_declared_perms.update(cap_data.get("permissions", []))
    for perm in permissions:
        if perm not in all_declared_perms:
            layer2_pass = False
    results.log("invoke-L2-Permissions", layer2_pass, "Permissions declaration check")

    # 第 3 层：远程 URL 白名单检查
    layer3_pass = True
    if url_patterns:
        all_remote_urls = set()
        for cap_file in cap_files:
            with open(cap_file, "r", encoding="utf-8") as f:
                cap_data = json.load(f)
            remote = cap_data.get("remote", {})
            all_remote_urls.update(remote.get("urls", []))
        for pattern in url_patterns:
            # 精确匹配或通配符覆盖
            if pattern not in all_remote_urls:
                # 检查是否有更宽松的模式覆盖
                covered = any(_pattern_covers(p, pattern) for p in all_remote_urls)
                if not covered:
                    layer3_pass = False
    results.log("invoke-L3-RemoteUrls", layer3_pass, "Remote URLs whitelist check")


def _pattern_covers(wider_pattern, narrower_pattern):
    """检查 wider_pattern 是否覆盖 narrower_pattern。

    例如 "http://localhost:*" 覆盖 "http://localhost:3000"。
    """
    # 将通配符转为正则
    regex = wider_pattern.replace("*", ".*").replace(".", r"\.")
    return bool(re.fullmatch(regex, narrower_pattern))
```

---

## 8. 常见误判与规避

| 误判场景 | 现象 | 规避方法 |
|----------|------|----------|
| capabilities.json 在子目录 | `capabilities/*.json` 未匹配到文件 | 调整 `invoke.capabilities_glob` 为 `**/capabilities/*.json` |
| Cargo.toml 注释含插件名 | 注释行含 `tauri-plugin-xxx` 导致误判已声明 | 解析时跳过 `#` 开头的行，只检查 `[dependencies]` 节内的实际依赖 |
| 权限名大小写不一致 | `allow-Log-Info` vs `allow-log-info` | 大小写敏感比较，Tauri 2.x 权限名约定为全小写 |
| remote.urls 使用变量 | `"${VITE_API_URL}"` 而非字面量 | 配置 `invoke.url_patterns` 时使用字面量模式，不依赖变量解析 |
| 插件名含下划线 | `tauri-plugin-shell-x` 命令名为 `plugin:shell_x` | 提取插件名时按下划线分割，取第一段匹配 |

## 9. 适用场景

- ✅ Tauri 2.x 桌面应用的 invoke 权限预检
- ✅ 新增 invoke 命令后的回归测试
- ✅ 运行时 invoke 错误的根因定位
- ❌ Tauri 1.x 项目（权限模型不同，需另行适配）
- ❌ 纯前端项目（无 invoke 调用）
- ❌ 使用 `tauri::command` 宏但未通过 `invoke_handler` 注册的命令（需另行检查 `lib.rs`）
