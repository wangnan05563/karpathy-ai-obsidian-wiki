# PowerShell 调用 cargo 的 stderr 处理规则（CODING-053）

> 复盘来源：PowerShell 脚本调用 `cargo build` 时设置 `$ErrorActionPreference = "Stop"`，cargo 的编译进度输出走 stderr（Rust 工具链惯例），被 PowerShell 误判为错误而中断脚本，导致构建无法完成。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `powershell_stderr` 字段读取，禁止在规则文件中硬编码工具名或参数。

## 触发场景

- PowerShell 脚本调用 `cargo` / `rustc` / `go build` 等输出 stderr 进度的工具
- 脚本在工具未实际报错时中断，报"非零退出码"或 stderr 输出
- `$ErrorActionPreference = "Stop"` 导致 cargo 进度输出触发停止
- CI/CD 流水线中 PowerShell 调用 Rust / Go 工具链失败
- Code Review 构建脚本中工具调用方式时

## 不适用场景

- 工具实际报错（退出码非 0 + stderr 含真实错误信息），此时中断是预期行为
- PowerShell 调用纯 stdout 输出的工具（如 `node` / `npm`，无 stderr 进度）
- Bash / Zsh 脚本（stderr 处理机制不同，规则不适用）
- Python 脚本调用 subprocess（用 `subprocess.run` 的 `stderr` 参数处理）

## 规则

### 规则 1：用 `Start-Process -NoNewWindow -Wait -PassThru` 替代直接调用

直接调用 `cargo build` 时，PowerShell 会将 stderr 写入错误流，配合 `$ErrorActionPreference = "Stop"` 会立即中断脚本。改用 `Start-Process -NoNewWindow -Wait -PassThru` 将 stderr 与 stdout 都写入控制台，不触发 PowerShell 错误流。

### 规则 2：避免 `$ErrorActionPreference = "Stop"` 拦截 stderr 进度

`$ErrorActionPreference = "Stop"` 会让 PowerShell 把任何写入错误流的内容（包括 cargo 的编译进度）视为终止错误。调用输出 stderr 进度的工具前，必须临时改为 `Continue` 或用 `Start-Process` 绕开。

### 规则 3：用退出码判断真实错误

工具是否失败必须以 `$process.ExitCode` 为准，而非 stderr 是否有输出。cargo / rustc / go build 等工具的 stderr 输出是进度信息（`Compiling xxx` / `Building xxx`），退出码 0 表示成功。

### 为什么

- **Rust 工具链 stderr 惯例**：cargo / rustc 将编译进度（`Compiling` / `Finished`）输出到 stderr 而非 stdout，这是 Unix 工具链传统（进度信息走 stderr，结果数据走 stdout，便于管道过滤）
- **PowerShell 错误流模型**：PowerShell 把任何写入错误流的内容当作"错误记录"，配合 `$ErrorActionPreference = "Stop"` 会立即抛出 `ActionPreferenceStopException` 中断脚本
- **直接调用的陷阱**：`cargo build` 直接调用时，PowerShell 重定向 stderr 到错误流，即使 cargo 编译成功（退出码 0），脚本仍被中断
- **Start-Process 隔离性**：`Start-Process` 启动独立进程，stderr 与 stdout 都直接写入控制台（不进入 PowerShell 的错误流），仅通过 `ExitCode` 反馈成功/失败

## 判断逻辑

```
调用 cargo / rustc / go build 等工具:
  IF 直接调用 + $ErrorActionPreference = "Stop":
      ❌ stderr 进度被误判为错误，脚本中断
  ELSE IF 用 Start-Process -NoNewWindow -Wait -PassThru:
      ✅ stderr 进度写入控制台，不触发 PowerShell 错误流
      ✅ 用 $process.ExitCode 判断真实错误（0=成功，非 0=失败）

工具失败判断:
  IF $process.ExitCode -ne 0:
      真实失败，抛错或中断
  ELSE IF $process.ExitCode -eq 0 + stderr 有输出:
      成功（stderr 是进度信息，非错误）
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `powershell_stderr.enabled` | `true` | 是否启用 stderr 处理守卫 |
| `powershell_stderr.severity` | `error` | 违规严重级别 |
| `powershell_stderr.recommended_invocation` | `Start-Process -NoNewWindow -Wait -PassThru` | 推荐的工具调用方式 |
| `powershell_stderr.forbidden_invocation` | `直接调用 + $ErrorActionPreference=Stop` | 禁止的工具调用方式 |
| `powershell_stderr.success_exit_code` | `0` | 成功退出码 |
| `powershell_stderr.stderr_progress_tools` | `cargo, rustc, go, gcc, cl` | 输出 stderr 进度的工具列表（逗号分隔） |
| `powershell_stderr.error_action_preference_for_tools` | `Continue` | 调用工具时 $ErrorActionPreference 的推荐值 |
| `powershell_stderr.exit_code_var` | `ExitCode` | 进程退出码属性名 |
| `powershell_stderr.require_explicit_exit_check` | `true` | 是否必须显式检查退出码 |

## 正确示例

### 用 `Start-Process` 调用 cargo

```powershell
# tauri-build.ps1
# 调用 cargo 必须用 Start-Process，避免 stderr 进度触发 $ErrorActionPreference=Stop
$ErrorActionPreference = "Stop"  # 脚本本身的错误处理保持严格

# ✅ 用 Start-Process 隔离 stderr，cargo 的 "Compiling xxx" 进度不触发错误流
$cargoResult = Start-Process cargo -ArgumentList "build" -NoNewWindow -Wait -PassThru
if ($cargoResult.ExitCode -ne 0) {
    throw "cargo build 失败，退出码: $($cargoResult.ExitCode)"
}
Write-Host "✅ cargo build 成功"
```

### 临时切换 `$ErrorActionPreference`

```powershell
# 若必须直接调用（如需管道处理输出），临时切换 $ErrorActionPreference
$ErrorActionPreference = "Stop"

# ✅ 调用前临时改为 Continue，避免 stderr 进度中断
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$output = cargo build 2>&1
$exitCode = $LASTEXITCODE
$ErrorActionPreference = $prevEAP

if ($exitCode -ne 0) {
    throw "cargo build 失败，退出码: $exitCode"
}
```

### 调用多个工具链

```powershell
# 调用 cargo + go build 都用 Start-Process，统一模式
$tools = @(
    @{ Name = "cargo"; Args = "build" },
    @{ Name = "go"; Args = "build ./..." }
)

foreach ($tool in $tools) {
    Write-Host "[$($tool.Name)] 构建中..."
    # ✅ 所有 stderr 进度工具都用 Start-Process
    $result = Start-Process -FilePath $tool.Name -ArgumentList $tool.Args -NoNewWindow -Wait -PassThru
    if ($result.ExitCode -ne 0) {
        throw "$($tool.Name) 失败，退出码: $($result.ExitCode)"
    }
    Write-Host "[$($tool.Name)] ✅ 成功"
}
```

## 错误示例

### 错误 1：直接调用 + `$ErrorActionPreference = "Stop"`

```powershell
# ❌ cargo 的 "Compiling xxx" 进度走 stderr，触发 Stop 中断脚本
$ErrorActionPreference = "Stop"
cargo build
# 抛出 ActionPreferenceStopException，脚本中断（即使 cargo 编译成功）
```

### 错误 2：仅依赖 stderr 判断错误

```powershell
# ❌ stderr 有输出不代表失败，cargo 成功时也输出 "Finished" 到 stderr
$output = cargo build 2>&1
if ($output) {
    throw "cargo build 失败: $output"  # 误判：cargo 成功时 $output 非空
}
```

### 错误 3：忽略退出码

```powershell
# ❌ 不检查 ExitCode，cargo 实际失败也不中断
Start-Process cargo -ArgumentList "build" -NoNewWindow -Wait
# 缺少 -PassThru 与 ExitCode 检查
```

### 错误 4：用 `2>$null` 静默 stderr

```powershell
# ❌ 静默 stderr 会丢失真实错误信息，排查困难
cargo build 2>$null
```

## 错误诊断速查表

| 现象 | 根因 | 修复动作 |
|------|------|---------|
| 脚本在 cargo 编译中途中断 | `$ErrorActionPreference=Stop` 拦截 stderr 进度 | 改用 `Start-Process` 或临时切换 EAP |
| 报 `ActionPreferenceStopException` | stderr 输出被当作终止错误 | 用 `Start-Process` 隔离 stderr |
| 脚本成功但报"失败" | 误用 stderr 输出判断失败 | 改用 `$process.ExitCode` 判断 |
| 真实错误被静默 | 用 `2>$null` 静默 stderr | 移除 `2>$null`，用 `Start-Process` 保留输出 |
| `go build` 同样中断 | go build 也输出 stderr 进度 | 同样用 `Start-Process` 调用 |

## 适用场景

- PowerShell 脚本调用 `cargo` / `rustc`（Rust 工具链）
- PowerShell 脚本调用 `go build`（Go 工具链）
- PowerShell 脚本调用 `gcc` / `cl`（C/C++ 编译器）
- 任何"进度走 stderr"的工具调用场景
- CI/CD 流水线中 PowerShell 调用编译工具链

## 适配新项目

- **Bash 项目**：规则不适用，Bash 默认不把 stderr 当错误
- **Python 脚本**：用 `subprocess.run(capture_output=True)` + `returncode` 判断
- **Node.js 脚本**：用 `child_process.spawn` + `exit` 事件判断
- **不同工具链**：`stderr_progress_tools` 追加新工具（如 `cmake` / `make` / `ninja`）
- **需要捕获输出的场景**：`Start-Process -RedirectStandardOutput` + `-RedirectStandardError` 分别重定向，仍用 `ExitCode` 判断
- **CI 环境**：CI 的 PowerShell 默认 `$ErrorActionPreference` 可能不同，显式设置避免依赖环境默认值
