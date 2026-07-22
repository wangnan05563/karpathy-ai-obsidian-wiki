# Tauri 2.x 桌面应用 E2E 测试规范

> 本规范基于 Tauri 2.x 桌面应用集成测试过程复盘提炼，覆盖从环境预检到错误诊断的完整测试流程。
> 所有测试参数从 `config.yaml` 的 `tauri` / `spa` / `health_check` / `invoke` / `disk_space` / `console_log` 节读取，不在代码中硬编码。
> 适配不同 Tauri 项目时仅需修改 config.yaml，无需改测试代码。

## 1. 测试目标

验证 Tauri 2.x 桌面应用在以下维度的可用性：
- **构建可重现**：SPA 产物与源码同步、Rust 编译可通过、Tauri 应用可启动
- **窗口可创建**：主窗口能正常打开并显示 SPA 内容
- **IPC 可调用**：`@tauri-apps/api` 的 `invoke` 调用能正确触达 Rust 命令并返回结果
- **错误可诊断**：stderr 日志、DevTools Console 日志可被采集并按关键词分类

## 2. 适用场景

- ✅ Tauri 2.x 桌面应用（含 SPA 前端 + Rust 后端）
- ✅ Windows / macOS / Linux 跨平台构建验证
- ✅ 通过 `@tauri-apps/api` 的 `invoke` 调用 Rust 命令的 IPC 场景
- ✅ 使用 `tauri-plugin-log` / `console.log` 输出日志的项目
- ❌ 纯 Web 项目（用 Playwright 直接测试，参见 SKILL.md 主流程）
- ❌ Tauri 1.x 项目（配置结构不同，需另行适配）

## 3. 测试阶段总览

| 阶段 | 名称 | 触发条件 | 通过条件 |
|------|------|----------|----------|
| 阶段 1 | 测试前预检 | `tauri_testing.enabled: true` | 环境验证 + SPA 产物时间戳 + 端口占用全部通过 |
| 阶段 2 | 构建与启动 | 阶段 1 通过 | SPA 构建 + Rust 编译 + Tauri 启动 + 后端健康检查全部通过 |
| 阶段 3 | 功能验证 | 阶段 2 通过 | 窗口创建 + invoke 权限 + 交互功能全部通过 |
| 阶段 4 | 错误诊断 | 阶段 3 失败或 `console_log.enabled: true` | stderr / Console 日志采集完毕并按规则分类 |
| 阶段 5 | 结果汇总 | 阶段 1-4 完成 | 输出 PASS/FAIL/SKIP 报告 + 修复建议 |
| 阶段 6 | 测试后清理 | 阶段 5 完成 | Tauri 进程已停止 + 临时日志已清理 |

> 阶段间为 DAG 依赖关系：阶段 1 的 critical 故障会中断后续所有阶段；阶段 4 在阶段 3 失败时仍需执行（用于诊断根因）。

---

## 4. 阶段 1：测试前预检

### 4.1 环境验证

检查 Tauri 桌面应用构建所需的全部依赖是否就绪。

| 检查项 | 验证方式 | 通过条件 | 失败修复建议 |
|--------|----------|----------|--------------|
| `cargo` 命令可用 | `cargo --version` | 退出码 0 且输出含 `cargo` | 安装 Rust 工具链：`https://rustup.rs/` |
| LLD 链接器可用 | `where.exe lld-link` (Windows) | 路径列表非空 | 安装 `lld` 包：`cargo install lld` 或安装 LLVM |
| `windres` 可用 (Windows) | `where.exe windres` | 路径列表非空 | 安装 MinGW-w64 或 w64devkit |
| 磁盘空间（debug） | `Get-PSDrive C` | 剩余空间 ≥ `disk_space.debug_min_gb` | 清理 `target/debug/` 与 `node_modules/` |
| 磁盘空间（release） | `Get-PSDrive C` | 剩余空间 ≥ `disk_space.release_min_gb` | 清理 `target/release/` 与 `node_modules/` |

**配置驱动**：所有阈值从 `config.yaml` 的 `disk_space` 节读取，不在代码中硬编码。

### 4.2 SPA 产物时间戳验证

> 防止 SPA 源码已修改但产物未重建，导致 Tauri 加载到旧版前端代码。

**验证流程**：
1. 遍历 `spa.source_dirs` 中配置的源码目录
2. 取每个源码文件的 `mtime`（最后修改时间戳）
3. 取 `spa.output_dir` 中产物的 `mtime`
4. 若任一源码 `mtime >` 产物 `mtime` → 判定需重建，输出最新修改的源码文件列表

**通过条件**：产物 `mtime` ≥ 所有源码 `mtime`，或 `spa.force_rebuild: true` 时强制重建后再次验证。

**失败修复建议**：执行 `tauri.build_script_path` 重新构建 SPA。

详细方法见 [spa-artifact-verification.md](spa-artifact-verification.md)。

### 4.3 端口占用检查

> 防止 `health_check.endpoint` 配置的端口被其他进程占用，导致 Tauri 后端服务启动失败。

**验证流程**：
1. 遍历 `service.required_ports` 中配置的端口
2. 用 `precheck.port_check_method`（默认 `Get-NetTCPConnection`）检查端口状态
3. 若端口已被占用且 `precheck.stop_old_process: true` → 停止占用进程
4. 若端口已被占用且 `precheck.stop_old_process: false` → 判定失败

**通过条件**：所有 `required_ports` 处于空闲状态（无 Listen 进程占用）。

**失败修复建议**：手动执行 `precheck.service_start_script` 的停止命令，或修改 `service.required_ports` 使用其他端口。

---

## 5. 阶段 2：构建与启动

### 5.1 SPA 构建

**验证流程**：
1. 读取 `tauri.build_script_path`（构建脚本路径）
2. 执行构建脚本（PowerShell 兼容性遵循 `powershell_compatibility.forbidden_syntaxes`）
3. 等待构建完成，超时由 `build.timeout_sec` 控制
4. 验证 `spa.output_dir/index.html` 存在且非空

**通过条件**：
- 构建脚本退出码为 0
- `spa.output_dir/index.html` 存在且文件大小 > 0

**失败修复建议**：
- 检查 `spa.package_name` 是否与 `package.json` 中的 `name` 字段一致
- 检查 `vite.config.ts` 的 `build.outDir` 是否指向 `spa.output_dir`
- 清理 `node_modules/.vite` 缓存后重试

### 5.2 Rust 编译

**验证流程**：
1. 进入 `tauri.src_tauri_dir` 目录
2. 执行 `cargo build`（debug 模式）或 `cargo build --release`（release 模式）
3. 监控 stderr 输出，匹配 `error[E` 开头的编译错误
4. 编译超时由 `tauri.compile_timeout_sec` 控制（默认 600s）

**通过条件**：
- 编译退出码为 0
- `target/debug/{exe_name}.exe` 或 `target/release/{exe_name}.exe` 存在

**失败修复建议**：
- `error[E0432]: unresolved imports` → 检查 `Cargo.toml` 依赖版本是否兼容 Tauri 2.x
- `error: linker 'lld-link' not found` → 安装 LLD 或在 `.cargo/config.toml` 中改用其他链接器
- `error: failed to run custom build command for 'xxx-sys'` → 安装系统级 C 库依赖

### 5.3 Tauri 应用启动

**验证流程**：
1. 执行 `target/debug/{exe_name}.exe`（或 release 路径）
2. 非阻塞启动（`subprocess.Popen`），将 stdout/stderr 重定向到临时日志文件
3. 等待 `tauri.startup_timeout_ms`（默认 15000ms）
4. 轮询检查进程是否存活

**通过条件**：
- 进程在 `tauri.startup_timeout_ms` 内未退出
- stderr 日志不含 `panicked at` 或 `thread 'main' has overflowed its stack`

**失败修复建议**：
- `failed to load window` → 检查 `tauri.conf.json` 的 `app.windows[0].url` 是否指向 SPA 产物路径
- `No such file or directory` → 检查 `tauri.conf.json` 的 `build.frontendDist` 是否与 `spa.output_dir` 一致
- `Permission denied` → 检查 exe 文件权限或 Windows Defender 隔离区

### 5.4 后端健康检查

**验证流程**：
1. 轮询 `health_check.endpoint`（默认 `http://localhost:{port}/health`）
2. 重试 `health_check.retry_count` 次（默认 30 次）
3. 每次重试间隔 `health_check.timeout` 毫秒（默认 1000ms）

**通过条件**：HTTP 响应状态码 == `health_check.expected_status`（默认 200）。

**失败修复建议**：
- 连接被拒绝 → 检查 `tauri.conf.json` 的 `app.security.csp` 是否阻止了后端请求
- 超时 → 增加 `health_check.retry_count` 或检查后端服务是否在 Tauri 启动后异步初始化
- 404 → 检查后端路由是否注册了 `/health` 端点

---

## 6. 阶段 3：功能验证

### 6.1 窗口创建验证

**验证流程**：
1. 通过进程名（`tauri.exe_name`）查找 Tauri 进程
2. 用 PowerShell `Get-Process` 验证进程存活
3. 用 Win32 API（`FindWindowW`）或 `Get-Process | Select MainWindowTitle` 验证主窗口已创建
4. 窗口标题应包含 `tauri.expected_window_title` 中配置的关键词

**通过条件**：
- Tauri 进程存活
- 主窗口标题非空且匹配 `tauri.expected_window_title`

**失败修复建议**：
- 进程存活但无窗口 → 检查 `tauri.conf.json` 的 `app.windows[0].visible` 是否为 `true`
- 窗口标题不匹配 → 检查 `tauri.conf.json` 的 `app.windows[0].title` 配置

### 6.2 invoke 权限验证

> Tauri 2.x 的 invoke 权限模型与 1.x 不同，必须在 `capabilities/*.json` 中显式声明。

**三层验证流程**：

| 层级 | 验证内容 | 通过条件 |
|------|----------|----------|
| 第 1 层 | `capabilities/*.json` 中 `permissions` 数组包含命令对应的插件权限 | 全部命令权限已声明 |
| 第 2 层 | `permissions` 数组包含 `allow-xxx` 形式的具体命令允许规则 | 全部 `allow-xxx` 已声明 |
| 第 3 层 | `remote.urls` 中包含测试 URL 模式（若启用远程 URL） | URL 模式匹配成功 |

**配置驱动**：
- `invoke.commands`：需验证的命令名列表（如 `["plugin:log|info", "plugin:http|fetch"]`）
- `invoke.permissions`：期望在 capabilities.json 中见到的权限名列表
- `invoke.url_patterns`：远程 URL 模式列表（如 `["http://localhost:*"]`）

**通过条件**：三层验证全部通过。

**失败修复建议**：详见 [invoke-permission-verification.md](invoke-permission-verification.md)。

### 6.3 交互功能验证

**验证流程**：
1. 通过 DevTools Protocol 或 `tauri-driver` 连接到 Tauri 窗口的 WebView
2. 遍历 `tauri.interaction_tests` 中配置的测试用例
3. 对每个用例：
   - 执行 `action`（如点击按钮、填写表单）
   - 等待 `wait_ms`
   - 验证 `expected_element` 可见或 `expected_api_called` 被调用

**通过条件**：全部用例的断言通过。

**失败修复建议**：
- 元素不可见 → 检查 WebView 是否成功加载 SPA 产物（看阶段 4 的 Console 日志）
- API 未被调用 → 检查前端代码的 `invoke` 调用是否触发，或 Rust 命令是否注册到 `invoke_handler`

---

## 7. 阶段 4：错误诊断

### 7.1 Tauri stderr 日志采集

**验证流程**：
1. 读取阶段 2 启动时重定向的 stderr 日志文件
2. 按行扫描，匹配 `console_log.error_keywords` 中配置的错误关键词
3. 对每个匹配行，提取时间戳、错误类型、错误消息

**通过条件**：stderr 日志不含任何 `error_keywords` 中的关键词（`warning` 不算失败）。

**失败修复建议**：根据匹配的关键词输出对应修复建议（参见 `failure_classification.rules`）。

### 7.2 DevTools Console 日志采集

**验证流程**：
1. 通过 CDP（Chrome DevTools Protocol）连接 Tauri WebView
2. 启用 `Runtime` 域，监听 `consoleAPICalled` 和 `exceptionThrown` 事件
3. 按 `console_log.prefixes` 过滤日志（如 `[Tauri]` / `[IPC]` / `[Plugin]`）
4. 收集 `console.error` 和 `console.warn` 级别的日志

**通过条件**：Console 日志不含 `console_log.error_keywords` 中的关键词。

**失败修复建议**：
- `Plugin not found` → 检查 `Cargo.toml` 是否添加了对应插件的依赖
- `not allowed` → 检查 `capabilities/*.json` 是否声明了对应权限（参见阶段 3.2）
- `URL: local` → 检查 `capabilities/*.json` 的 `remote.urls` 是否包含测试 URL

### 7.3 invoke 错误分类

**错误关键词映射**：

| 错误消息关键词 | 失败类型 | 修复建议 |
|----------------|----------|----------|
| `Plugin not found` | invoke_layer_1 | 在 `Cargo.toml` 添加插件依赖，重新编译 |
| `not allowed` | invoke_layer_2 | 在 `capabilities/*.json` 的 `permissions` 数组中添加 `allow-xxx` |
| `URL: local` | invoke_layer_3 | 在 `capabilities/*.json` 的 `remote.urls` 中添加测试 URL 模式 |
| `command not found` | command_not_registered | 在 `lib.rs` 的 `invoke_handler` 中注册命令 |
| `serialization error` | serde_mismatch | 检查 Rust 命令参数类型与前端 `invoke` 调用参数是否一致 |

---

## 8. 阶段 5：结果汇总

### 8.1 报告格式

```
## Tauri Desktop Test Report
- Phase 1 Pre-check: PASS/FAIL/SKIP (details)
- Phase 2 Build & Start: PASS/FAIL/SKIP (details)
- Phase 3 Functional: PASS/FAIL/SKIP (details)
- Phase 4 Diagnostics: PASS/FAIL/SKIP (details)
- Total: N tests | Passed: X | Failed: Y | Skipped: Z
```

### 8.2 状态判断标准

| 状态 | 判断标准 |
|------|----------|
| PASS | 该阶段所有断言通过 |
| FAIL | 该阶段至少一个 critical 断言失败 |
| SKIP | 该阶段被 `enabled: false` 跳过，或前置阶段 critical 失败导致无法执行 |

### 8.3 修复建议输出

每条失败项必须包含：
- 失败的断言名称
- 实际值 vs 期望值
- 匹配的失败分类规则（来自 `failure_classification.rules`）
- 对应的修复建议（来自 `failure_classification.suggestions`）

---

## 9. 阶段 6：测试后清理

### 9.1 Tauri 进程停止

**验证流程**：
1. 用 `Stop-Process -Name {tauri.exe_name}` 停止 Tauri 进程
2. 等待 2 秒后用 `Get-Process` 验证进程已退出
3. 若进程仍存活，用 `taskkill /F /T /PID {pid}` 强制终止

### 9.2 临时日志清理

**清理范围**：
- 阶段 2 重定向的 stderr/stdout 日志文件
- 阶段 4 采集的 Console 日志临时文件
- Tauri 编译缓存（可选，由 `tauri.cleanup_target_dir: true` 控制）

**通过条件**：临时文件已删除，`target/debug/` 或 `target/release/` 大小未超过 `disk_space.cleanup_threshold_gb`。

---

## 10. 配置示例

完整的 Tauri 桌面测试配置示例见 `config.yaml` 的 `tauri` / `spa` / `health_check` / `invoke` / `disk_space` / `console_log` 节。

### 关键配置块速查

```yaml
tauri:
  enabled: true
  exe_name: "karpathy-wiki"
  src_tauri_dir: "karpathy-wiki/src-tauri"
  build_script_path: "karpathy-wiki/scripts/前端构建.bat"
  expected_window_title: "Karpathy"
  startup_timeout_ms: 15000
  compile_timeout_sec: 600

spa:
  package_name: "karpathy-wiki-frontend"
  output_dir: "karpathy-wiki/api/public"
  source_dirs:
    - "karpathy-wiki/frontend/src"
  force_rebuild: false

health_check:
  endpoint: "http://localhost:3000/health"
  retry_count: 30
  timeout: 1000
  expected_status: 200

invoke:
  commands:
    - "plugin:log|info"
    - "plugin:http|fetch"
  permissions:
    - "allow-log-info"
    - "allow-http-fetch"
  url_patterns:
    - "http://localhost:*"

disk_space:
  debug_min_gb: 5
  release_min_gb: 10
  cleanup_threshold_gb: 20

console_log:
  prefixes:
    - "[Tauri]"
    - "[IPC]"
    - "[Plugin]"
  error_keywords:
    - "Plugin not found"
    - "not allowed"
    - "URL: local"
    - "command not found"
    - "serialization error"
    - "panicked at"
```

---

## 11. 与 SKILL.md 主流程的关系

- Tauri 桌面测试是 SKILL.md 主流程的**可选扩展阶段**，仅在 `tauri.enabled: true` 时执行
- 阶段 1-6 可与 SKILL.md 的标准 6 阶段测试流程并行或串行
- 测试结果合并到统一的 `test_result.json`，按 `phase` 字段区分
- 失败分类复用 `failure_classification.rules`，通过 `type` 字段标识 Tauri 特有失败类型

## 12. 故障排查速查表

| 现象 | 可能原因 | 验证阶段 | 修复步骤 |
|------|----------|----------|----------|
| Tauri 启动后立即退出 | Rust 编译错误或窗口配置错误 | 阶段 2 / 阶段 4 | 查看 stderr 日志中的 `panicked at` |
| 窗口创建但白屏 | SPA 产物未构建或路径错误 | 阶段 1.2 / 阶段 4 | 重新构建 SPA，检查 `frontendDist` 配置 |
| invoke 调用报 `Plugin not found` | Cargo.toml 缺少插件依赖 | 阶段 3.2 / 阶段 4 | 添加 `tauri-plugin-xxx` 依赖并重新编译 |
| invoke 调用报 `not allowed` | capabilities.json 缺少权限声明 | 阶段 3.2 / 阶段 4 | 在 `permissions` 数组中添加 `allow-xxx` |
| invoke 调用报 `URL: local` | remote.urls 未匹配测试 URL | 阶段 3.2 / 阶段 4 | 在 `remote.urls` 中添加 URL 模式 |
| 后端健康检查超时 | 后端服务未在 Tauri 启动时初始化 | 阶段 2.4 | 增加 `health_check.retry_count` 或检查后端初始化逻辑 |
| 编译报 `linker 'lld-link' not found` | 缺少 LLD 链接器 | 阶段 1.1 / 阶段 2.2 | 安装 LLVM 或在 `.cargo/config.toml` 改用 `msvc-link` |
