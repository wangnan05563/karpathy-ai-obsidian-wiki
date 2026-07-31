# 测试协议与历史复盘

> 本文档从 SKILL.md 拆分而来，含 5 个测试协议 + 2 个历史复盘章节。
> 当测试流程遇到协议相关问题或需要参考历史复盘时按需加载。
> SKILL.md 入口文件保留章节导航链接。

## 目录

- [前置检查协议（Pre-flight Check Protocol）](#前置检查协议pre-flight-check-protocol)
- [测试用例同步协议（Test Case Sync Protocol）](#测试用例同步协议test-case-sync-protocol)
- [失败分类协议（Failure Classification Protocol）](#失败分类协议failure-classification-protocol)
- [服务管理协议（Service Management Protocol）](#服务管理协议service-management-protocol)
- [搜索结果交叉验证协议（Search Result Cross-Verification Protocol）](#搜索结果交叉验证协议search-result-cross-verification-protocol)
- [v2 导航栏改造测试复盘（2026-07-22）](#v2-导航栏改造测试复盘2026-07-22)
- [文件夹上传批量编译测试复盘（2026-07-22）](#文件夹上传批量编译测试复盘2026-07-22)

## 前置检查协议（Pre-flight Check Protocol）

> 基于 v2 导航栏改造复盘提炼，防止 E2E 测试在服务未就绪时运行导致全部用例误报失败。

仅在 `precheck.enabled: true` 时执行。**测试入口前置检查**（在阶段 1 构建之前执行），通过端口监听 + 健康检查 + 浏览器可启动性三层验证，确保后续测试在就绪环境上运行。

### 子阶段：测试入口前置检查

1. **端口监听检查**：遍历 `precheck.required_ports`，用 `precheck.port_check_method` 检测每个端口状态是否为 `precheck.port_check_state`
2. **健康检查**：调用 `precheck.health_check_endpoint`，验证 HTTP 响应状态码 == `precheck.health_check_expected_status`
3. **浏览器可启动检查（可选）**：若 `precheck.browser_launch_check: true`，尝试启动浏览器并访问 `about:blank`，验证 Playwright 环境可用
4. **失败处理**：
   - 若 `precheck.auto_start_on_failure: true`：调用 `precheck.service_start_script` 启动服务，按 `precheck.port_poll_interval_ms` 轮询端口，最长等待 `precheck.startup_timeout_ms` 毫秒
   - 否则：中止测试，输出诊断日志
5. **日志输出**：必须输出诊断信息（端口状态、健康检查响应），便于排查环境问题

### 参数表（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `precheck.enabled` | `true` | 是否启用前置检查协议 |
| `precheck.required_ports` | `[3000, 5173]` | 必须监听的端口列表 |
| `precheck.port_check_state` | `Listen` | 端口期望状态（Listen / Bound） |
| `precheck.port_check_method` | `Get-NetTCPConnection` | 端口检测方法（PowerShell cmdlet） |
| `precheck.health_check_endpoint` | `/health` | 健康检查端点路径 |
| `precheck.health_check_expected_status` | `200` | 健康检查期望 HTTP 状态码 |
| `precheck.startup_timeout_ms` | `30000` | 启动后最长等待毫秒数 |
| `precheck.port_poll_interval_ms` | `1000` | 端口轮询间隔毫秒数 |
| `precheck.browser_launch_check` | `true` | 是否执行浏览器可启动检查 |
| `precheck.service_start_script` | `automation.ps1 -Action start` | 服务启动脚本 |
| `precheck.auto_start_on_failure` | `true` | 检查失败时是否自动启动服务 |

### 配置示例

```yaml
precheck:
  enabled: true
  required_ports:
    - 3000
    - 5173
  port_check_state: "Listen"
  port_check_method: "Get-NetTCPConnection"
  health_check_endpoint: "/health"
  health_check_expected_status: 200
  startup_timeout_ms: 30000
  port_poll_interval_ms: 1000
  browser_launch_check: true
  service_start_script: "automation.ps1 -Action start"
  auto_start_on_failure: true
```

## 测试用例同步协议（Test Case Sync Protocol）

> 基于 v2 改造复盘提炼，防止代码变更影响 DOM 后测试用例引用已删除的选择器。

仅在 `test_sync.enabled: true` 时执行。**代码变更后测试同步验证**（在阶段 5 补充测试中执行），通过 git diff 扫描选择器变更并交叉检查测试用例引用，避免测试引用失效选择器。

### 子阶段：代码变更后测试同步验证

1. **选择器变更识别**：用 `test_sync.selector_patterns` 中配置的正则模式，扫描 git diff 中 class / id / 层级 / data-testid 的删除或修改
2. **测试用例引用扫描**：按 `test_sync.test_file_patterns` 匹配测试文件，Grep 查找引用了被删除选择器的用例
3. **失败处理**：命中即判定为同步失败，必须更新测试用例（若 `test_sync.stale_selector_threshold: 0`，零容忍）
4. **静默错误检测**：若 `test_sync.silent_failure_forbidden: true`，扫描测试用例的 try/except 块，确认 except 分支未静默吞错（必须 `record(..., False, str(e))`）
5. **同 commit 验证**：若 `test_sync.require_same_commit: true`，检查 commit 中是否同时包含代码与测试用例修改，避免代码先行/测试滞后的不对称提交

### 参数表（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `test_sync.enabled` | `true` | 是否启用测试同步协议 |
| `test_sync.test_file_patterns` | `**/test_*.py,**/test_*.ts,**/*.spec.ts,**/*.test.ts` | 测试文件 glob 匹配模式（逗号分隔） |
| `test_sync.selector_patterns` | `\.[-\w]+, #[-\w]+, [class="[^"]+"], data-testid="[^"]+"` | 选择器变更识别正则（逗号分隔） |
| `test_sync.require_same_commit` | `true` | 是否要求代码与测试同 commit 提交 |
| `test_sync.silent_failure_forbidden` | `true` | 是否禁止 except 分支静默吞错 |
| `test_sync.stale_selector_threshold` | `0` | 失效选择器容忍阈值（0 = 零容忍） |

### 配置示例

```yaml
test_sync:
  enabled: true
  test_file_patterns:
    - "**/test_*.py"
    - "**/test_*.ts"
    - "**/*.spec.ts"
    - "**/*.test.ts"
  selector_patterns:
    - '\.[-\w]+'
    - '#[-\w]+'
    - '[class="[^"]+"]'
    - 'data-testid="[^"]+"'
  require_same_commit: true
  silent_failure_forbidden: true
  stale_selector_threshold: 0
```

## 失败分类协议（Failure Classification Protocol）

> 基于 v2 改造复盘提炼，标准化测试失败的分类与处理流程。

仅在 `failure_classification.enabled: true` 时执行。**测试失败后自动分类**（在阶段 6 结果汇总中执行），按错误消息模式匹配失败类型，并输出对应的修复建议。

### 子阶段：测试失败后自动分类

1. **失败类型枚举**：`connection_refused` / `selector_not_found` / `assertion_failed` / `timeout` / `browser_crash` / `encoding_corrupted` / `config_mismatch`
2. **分类规则**：按 `failure_classification.rules` 中的模式匹配错误消息，每条规则包含 `type` / `pattern` / `suggestion` 三元组
3. **处理建议**：每种失败类型对应 `failure_classification.suggestions` 中的修复建议（命令或操作步骤）
4. **自动修复触发**：若 `failure_classification.auto_fix: true`，对 `selector_not_found` 类型自动触发测试用例同步检查（衔接 Test Case Sync Protocol）

### 失败类型 + 模式 + 建议对照表

| 失败类型 | 匹配模式 | 修复建议 |
|----------|----------|----------|
| `connection_refused` | `ERR_CONNECTION_REFUSED`, `ECONNREFUSED` | 运行 `automation.ps1 -Action start` 启动服务 |
| `selector_not_found` | `TimeoutError.*waiting for selector`, `Element not found` | 检查代码是否删除了该选择器，同步更新测试用例 |
| `assertion_failed` | `AssertionError`, `expect(*) to be` | 检查断言预期值是否与实际行为一致 |
| `timeout` | `TimeoutError`, `Exceeded timeout` | 增加超时时间或优化等待策略 |
| `browser_crash` | `Target closed`, `Browser crashed` | 检查 Chromium 启动参数，参考 `headless_crash_guard` |
| `encoding_corrupted` | `U+FFFD`, `锟斤拷`, `乱码` | 运行 `node scripts/check-encoding.js --fix` |
| `config_mismatch` | `config.*not.*found`, `undefined` | 检查 config.yaml 与 defaults.yaml 配置项 |

### 参数表（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `failure_classification.enabled` | `true` | 是否启用失败分类协议 |
| `failure_classification.rules` | 见配置示例 | 失败类型匹配规则列表（type + pattern + suggestion） |
| `failure_classification.suggestions` | 见配置示例 | 失败类型对应的修复建议映射 |
| `failure_classification.auto_fix` | `true` | 是否对 selector_not_found 自动触发测试同步检查 |

### 配置示例

```yaml
failure_classification:
  enabled: true
  auto_fix: true
  rules:
    - type: "connection_refused"
      pattern: "ERR_CONNECTION_REFUSED|ECONNREFUSED"
      suggestion: "运行 automation.ps1 -Action start 启动服务"
    - type: "selector_not_found"
      pattern: "TimeoutError.*waiting for selector|Element not found"
      suggestion: "检查代码是否删除了该选择器，同步更新测试用例"
    - type: "assertion_failed"
      pattern: "AssertionError|expect\\(.*\\) to be"
      suggestion: "检查断言预期值是否与实际行为一致"
    - type: "timeout"
      pattern: "TimeoutError|Exceeded timeout"
      suggestion: "增加超时时间或优化等待策略"
    - type: "browser_crash"
      pattern: "Target closed|Browser crashed"
      suggestion: "检查 Chromium 启动参数，参考 headless_crash_guard"
    - type: "encoding_corrupted"
      pattern: "U\\+FFFD|锟斤拷|乱码"
      suggestion: "运行 node scripts/check-encoding.js --fix"
    - type: "config_mismatch"
      pattern: "config.*not.*found|undefined"
      suggestion: "检查 config.yaml 与 defaults.yaml 配置项"
    - type: "epipe_error"
      pattern: "EPIPE|broken pipe|exit code -1"
      suggestion: "移除管道重新直接运行，将输出重定向到文件后读取"
  suggestions:
    connection_refused: "运行 automation.ps1 -Action start 启动服务"
    selector_not_found: "检查代码是否删除了该选择器，同步更新测试用例"
    assertion_failed: "检查断言预期值是否与实际行为一致"
    timeout: "增加超时时间或优化等待策略"
    browser_crash: "检查 Chromium 启动参数，参考 headless_crash_guard"
    encoding_corrupted: "运行 node scripts/check-encoding.js --fix"
    config_mismatch: "检查 config.yaml 与 defaults.yaml 配置项"
    epipe_error: "移除管道重新直接运行，将长时进程输出重定向到文件后读取"
```

## 服务管理协议（Service Management Protocol）

> 基于 v2 改造复盘提炼，标准化测试过程中的服务生命周期管理。

仅在 `service_management.enabled: true` 时执行。**测试过程服务管理**（贯穿阶段 1-6），覆盖服务状态检测、端口冲突预防、日志重定向残留清理、测试后清理四个环节。

### 子阶段：测试过程服务管理

1. **服务状态检测**：测试前、测试中、测试后分别检测服务状态（端口监听 + 健康检查）
2. **端口冲突预防**：若 `service_management.stop_old_process: true`，测试启动前先停止占用 `precheck.required_ports` 的旧进程，避免端口冲突导致新服务启动失败
3. **日志重定向清理**：若 `service_management.cleanup_residual: true`，测试后清理因 `pnpm run dev` 等日志重定向产生的 cmd.exe 残留进程（按 `service_management.residual_match_pattern` 匹配命令行）
4. **测试后清理**：若 `service_management.cleanup_after_test: true`，测试完成后调用 `service_management.stop_script` 停止服务（仅当 `service_management.keep_running: false` 时执行）

### 参数表（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `service_management.enabled` | `true` | 是否启用服务管理协议 |
| `service_management.stop_old_process` | `true` | 测试启动前是否停止占用端口的旧进程 |
| `service_management.cleanup_residual` | `true` | 是否清理日志重定向残留进程 |
| `service_management.cleanup_after_test` | `false` | 测试后是否停止服务（受 keep_running 控制） |
| `service_management.keep_running` | `true` | 测试后是否保持服务运行（true 时即使 cleanup_after_test=true 也不停止） |
| `service_management.residual_match_pattern` | `pnpm run dev` | 残留进程命令行匹配模式 |
| `service_management.stop_script` | `automation.ps1 -Action stop` | 服务停止脚本 |

### 配置示例

```yaml
service_management:
  enabled: true
  stop_old_process: true
  cleanup_residual: true
  cleanup_after_test: false
  keep_running: true
  residual_match_pattern: "pnpm run dev"
  stop_script: "automation.ps1 -Action stop"
```

## 搜索结果交叉验证协议（Search Result Cross-Verification Protocol）

> 基于 P0/P1/P2 目录结构优化复盘提炼，防止单一搜索方法因工具限制（路径含特殊字符、输出截断、未入库文件）返回假阴性，导致测试用例误判失败或漏检真实问题。所有参数从 `config.search_cross_verification` 读取，不在代码中硬编码工具名或阈值。

仅在 `search_cross_verification.cross_verify_required: true` 时执行。**搜索结果未找到时的强制交叉验证**（贯穿所有测试阶段），覆盖 Glob / Grep / LS / Test-Path 四种方法的互相验证，确保"未找到"结论经过至少两种方法确认。

### 适用场景

- 测试用例通过 Glob 查找文件未命中，需确认是否因路径含特殊字符（`+` / `(` / `)` / `[` / `]`）导致通配符转义失败
- 测试用例通过 Grep 搜索文件内容未命中，需确认是否因文件未入库或被 .gitignore 排除
- 测试用例通过 LS 列目录未命中目标，需确认是否因输出超长被截断（> `ls_truncate_threshold`）
- 验证文件/目录是否存在时，单一方法返回"不存在"必须用另一种方法复核

### 验证矩阵

| 工具 | 适用场景 | 限制 |
|------|----------|------|
| Glob | 文件名模式匹配（支持 `*` / `?` / `[]`） | 路径含 `glob_escape_chars` 中的特殊字符时可能转义失败 |
| Grep | 文件内容搜索（正则匹配） | 无法搜索未入库的文件（受 .gitignore 与索引影响） |
| LS | 目录列表（递归枚举） | 输出超 `ls_truncate_threshold` 字符时可能截断 |
| Test-Path | 精确路径存在性判断 | 需已知完整路径，不支持通配符 |

### 验证流程

1. **主搜索方法未找到目标**：任一 `primary_tools`（Glob / Grep / LS）返回空结果或退出码 1
2. **触发交叉验证**：从 `fallback_tools`（PowerShell `Test-Path` / `Resolve-Path`）中选择互补方法
3. **互补方法选择规则**：
   - Glob 失败 → 用 `Test-Path` 精确验证（避免通配符转义问题）
   - Grep 失败 → 用 `LS` 或 `Test-Path` 验证文件存在性（排除索引未入库问题）
   - LS 失败 → 用 `Glob` 精确模式验证（避免输出截断）
4. **结果汇总**：
   - 互补方法找到目标 → 主方法为假阴性，记录工具限制原因，测试继续
   - 互补方法也未找到 → 确认为真阴性，按测试用例预期处理
5. **日志输出**：交叉验证必须记录主方法、互补方法、各自结果、最终判定

### 关键原则

- **任一搜索方法未找到目标时，必须用另一种方法交叉验证**，禁止仅凭单一方法返回空即判定目标不存在
- **Glob 模式中的特殊字符**（`+` / `(` / `)` / `[` / `]`）必须按 `glob_escape_chars` 配置转义，否则视为无效搜索
- **LS 输出超 `ls_truncate_threshold`** 时自动降级为 Glob 精确模式，避免截断导致的假阴性
- **Grep 内容搜索**应同时尝试 `grep_content_patterns` 中的多种模式（如 `export class {name}` 与 `export.*{name}`），避免单一模式遗漏

### 失败处理

- **主方法假阴性**：在测试报告中标注工具限制原因，更新 `verification_matrix` 中的 limitation 说明
- **互补方法也失败**：确认为真阴性，按测试用例预期失败处理，输出诊断日志（主方法输出、互补方法输出、尝试的模式列表）
- **Glob 转义失败**：检查路径是否含 `glob_escape_chars`，重新构造转义后的模式重试
- **Grep 未入库**：检查文件是否被 .gitignore 排除或未 git add，必要时用 `Test-Path` 直接验证文件系统存在性

## v2 导航栏改造测试复盘（2026-07-22）

> 本节基于 v2 导航栏改造（折叠/展开双模式 + 12 图标导航）的 E2E 测试执行过程复盘，提炼可复用的固定流程与失败模式。

### 成功执行任务的完整步骤

| 步骤 | 操作 | 验证点 | 对应协议 |
|------|------|--------|----------|
| 1 | 端口监听检查（3000/5173） | 两端口均处于 Listen 状态 | Pre-flight Check |
| 2 | 健康检查（GET /health） | HTTP 200 响应 | Pre-flight Check |
| 3 | 浏览器启动检查（about:blank） | Playwright 环境可用 | Pre-flight Check |
| 4 | 停止占用端口的旧进程 | 无残留 cmd.exe / node.exe 占用端口 | Service Management |
| 5 | 启动后端 + 前端服务 | 端口在 startup_timeout_ms 内就绪 | Service Management |
| 6 | 执行阶段 1-6 测试用例 | 全部断言通过 | 标准流程 |
| 7 | 失败时按错误消息模式分类 | 输出对应修复建议 | Failure Classification |
| 8 | selector_not_found 自动触发同步检查 | 检测 git diff 选择器变更 | Test Case Sync |
| 9 | 测试后清理残留进程 | 无日志重定向 cmd.exe 残留 | Service Management |

### 不确定性与失败点

1. **ERR_CONNECTION_REFUSED**：服务未启动或启动未完成时，所有用例报连接拒绝 → 已由 Pre-flight Check 协议在测试入口拦截
2. **选择器失效**：v2 改造删除/重命名了 `.tab-btn` / `.nav-toggle` 等选择器后，旧测试用例引用失效 → 已由 Test Case Sync 协议在阶段 5 检测
3. **静默吞错**：测试用例 except 分支用 `pass` 吞掉异常，导致用例"假通过" → 已由 Test Case Sync 协议的 silent_failure_forbidden 检测
4. **端口冲突**：旧服务未停止即启动新服务，导致新服务绑定端口失败 → 已由 Service Management 协议的 stop_old_process 预防
5. **日志重定向残留**：`pnpm run dev > log.txt 2>&1` 产生的 cmd.exe 残留进程占用资源 → 已由 Service Management 协议的 cleanup_residual 清理

### 可抽象的固定流程

#### 前置检查流程（Pre-flight Check Flow）

```
端口检查 → 健康检查 → 浏览器检查 → (失败) 自动启动服务 → 轮询端口 → 通过/中止
```

该流程与具体业务无关，可作为所有 E2E 测试的统一入口。

#### 测试同步流程（Test Case Sync Flow）

```
git diff 选择器变更 → Grep 测试文件引用 → 命中失效引用 → 检测静默吞错 → 同 commit 验证 → 失败/通过
```

该流程与具体页面无关，可作为所有代码变更后的测试同步验证。

### 适用场景

- v2 导航栏改造后的回归测试（折叠/展开切换、12 图标导航、tooltip、localStorage 持久化）
- 服务重启或端口变更后的环境就绪验证
- 代码变更涉及 DOM 选择器删除/重命名时的测试同步检查
- 测试失败原因不明确时按错误消息模式自动分类
- 长时间测试流程中的服务生命周期管理

### 不适用场景

- 纯静态 HTML 页面（无服务启动需求，Pre-flight Check 仅需浏览器检查）
- 无 git 仓库的项目（Test Case Sync 的 git diff 扫描不适用）
- 单次性临时测试（Service Management 的残留清理不必要）
- 已知失败原因明确无需分类的场景（Failure Classification 的分类开销不必要）

## 文件夹上传批量编译测试复盘（2026-07-22）

> 本节基于文件夹上传批量编译功能的 E2E 测试执行过程复盘，提炼可复用的六阶段测试流程与失败模式。

### 成功执行任务的完整步骤

| 步骤 | 操作 | 验证点 | 对应阶段 |
|------|------|--------|----------|
| 1 | 预检查（环境/端口/配置/PowerShell） | 所有预检项通过 | 阶段 1：预检查 |
| 2 | 服务启动（非阻塞模式） | 端口在 startup_timeout_ms 内就绪 | 阶段 2：服务启动 |
| 3 | API 端点测试（10 个端点） | 全部返回 200 | 阶段 3：动态验证 |
| 4 | 路由注册验证 + 类型同步验证 | 后端路由全部注册、前后端 types.ts 对齐 | 阶段 3：静态验证（并行） |
| 5 | UI 元素验证（11 个页面） | expected_elements 选择器全部存在 | 阶段 3：动态验证 |
| 6 | SSE 事件流验证 | batch_start→file_start→progress×8→file_done→file_complete→batch_done 完整 | 阶段 3：动态验证 |
| 7 | 编码乱码检测 + 危险操作测试 + 滚动容器测试 + SPA 跳转测试 + 检查更新测试 | 全部通过 | 阶段 4：专项验证 |
| 8 | 测试后清理（停止服务+清理临时文件） | 无残留进程 | 阶段 5：清理 |

### 不确定性与失败点

1. **端口占用冲突**：5173 被其他项目占用，被迫改用 5174，导致 config.yaml 中硬编码的 5173 失效 → 已由 port_conflict_resolution 配置块的自动迁移策略解决
2. **Vite proxy SSE 中断**：简写形式 `'/api': 'http://localhost:3000'` 缺少 changeOrigin/timeout，导致 SSE 长连接被中断，出现 'Failed to fetch' → 已由 vite_proxy_check 配置块检测
3. **PRESETS_PATH 路径解析错误**：api/src/routes/ai.ts:13 少一个 '../'，导致 llm-presets.json 找不到，API 启动崩溃 → 已由 compile_artifact_check 配置块检测路径解析
4. **PowerShell 5.1 语法限制**：不支持 &&/||，需用 ; 分隔 → 已由 powershell_compatibility 配置块检测
5. **bat 脚本 pause 阻塞**：自动化调用时 pause 等待用户按键 → 已由 bat_script.bypass_pause 配置解决
6. **日志重定向 cmd 进程残留**：taskkill 主进程后，日志重定向 cmd 仍持有句柄 → 已由 process_cleanup 配置块的 Get-CimInstance Win32_Process 命令行匹配清理
7. **Vite dev server 优先加载 .js 编译产物**：src 下同时存在 .ts 和 .js 时，Vite 直接读 .js 导致旧版代码被加载 → 已由 compile_artifact_check 配置块检测

### 可抽象的固定流程

#### 六阶段测试流程

```
阶段 1：预检查（环境/端口/配置/PowerShell）→ 并行执行
    ↓（全过才继续）
阶段 2：服务启动（非阻塞+端口轮询）
    ↓
阶段 3：动态验证（API+UI+SSE） ← 并行 → 静态验证（路由注册+类型同步）
    ↓（API+UI 通过才继续）
阶段 4：专项验证（编码+危险操作+滚动+SPA+检查更新）
    ↓
阶段 5：清理（停止服务+清理临时文件）
```

#### 故障分类与诊断决策树

```
服务未启动 → 检查端口占用+旧进程残留（process_cleanup）
SSE 中断 → 检查 Vite proxy 配置（vite_proxy_check：简写形式 vs 对象形式）
API 崩溃 → 检查路径解析（compile_artifact_check：import.meta.url vs process.cwd）
类型不同步 → 检查前后端 types.ts interface 字段（type_sync_check）
```

### 适用场景

- Vue 3 + Vite + Fastify 全栈项目
- SPA 手动路由（无 vue-router）项目
- SSE 长连接项目
- 多主题切换项目
- Windows PowerShell 环境项目

### 不适用场景

- 纯后端项目（无前端 UI 元素验证）
- 使用 vue-router 的 SPA（路由注册验证逻辑不同）
- Linux/macOS 环境（PowerShell 约束不适用，需改为 bash 兼容）
- 无 SSE 的项目（SSE 事件流验证不适用）
- 容器化部署项目（服务生命周期由容器编排管理，不需手动启停）

### 阶段间 DAG 依赖关系

测试阶段间存在有向无环图（DAG）依赖关系：

| 阶段 | 依赖前置阶段 | 故障传播规则 |
|------|-------------|-------------|
| 预检查 | 无（并行执行） | critical 故障中断后续所有阶段 |
| 服务启动 | 预检查全过 | critical 故障中断后续所有阶段 |
| API 端点测试 | 服务启动 | critical 故障中断 UI/SSE/专项验证 |
| 路由注册验证 + 类型同步验证 | 无（与服务启动并行，静态检查） | warning/suggestion 不中断 |
| UI 元素验证 + SSE 事件流验证 | 服务启动 + API 端点测试通过 | critical 故障中断专项验证 |
| 编码乱码检测 + 危险操作测试 + 滚动容器测试 + SPA 跳转测试 + 检查更新测试 | UI 元素验证通过 | warning/suggestion 不中断 |
| 测试后清理 | 最后执行（无论前序成败） | 必须执行 |

关键规则：
- **critical 故障**从任意阶段向上传播，中断后续依赖阶段
- **warning/suggestion**不中断后续阶段
- **测试后清理**必须执行（即使前序阶段失败）

### 新增配置块说明

#### vite_proxy_check（Vite Proxy 配置检查）

检测 Vite proxy 配置是否为对象形式（含 changeOrigin/timeout/proxyTimeout），避免 SSE 长连接中断。

#### port_conflict_resolution（端口冲突自动迁移）

配置端口被占用时的自动迁移策略（检测实际可用端口并更新 config）。

#### compile_artifact_check（编译产物污染检测）

检测 src 下是否同时存在 .ts 和 .js 文件，避免 Vite 加载旧编译产物；检测路径解析是否采用 import.meta.url 三级策略。

#### process_cleanup 增强（进程残留清理增强）

在 service_lifecycle 基础上增强：日志重定向 cmd 残留清理策略（Get-CimInstance Win32_Process 命令行匹配）。
