# PowerShell stderr 处理审查规则（BR-045~047）

> 复盘来源：Tauri 2.x 桌面应用集成中，PowerShell 构建脚本（`tauri-build-*.ps1`）在 `$ErrorActionPreference = 'Stop'` 模式下直接用 `& cargo build` 调用外部工具，cargo 的 stderr 输出会被 PowerShell 误判为错误流终止脚本执行；或用 `& cargo ... 2>&1 | Out-Host` 合并流后丢失 stderr 的错误语义（无法区分 cargo 的 stderr 警告 vs 真正错误），导致构建失败时定位困难。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"PowerShell stderr 处理审查参数（powershell_stderr）"章节读取，禁止在本规则文件硬编码具体命令名或工具列表。

## Trigger Keywords

$ErrorActionPreference, Start-Process, -NoNewWindow, -Wait, -PassThru, 2>&1, Out-Host, cargo build, cargo tauri, rustc, & cargo, & rustc, Tee-Object, stderr, error stream, PowerShell error action

## Rules

### BR-045: 调用外部工具必须用 `Start-Process -NoNewWindow -Wait -PassThru` 而非直接 `&` 调用

- **Severity**: critical
- **Description**: PowerShell 脚本中调用 `cargo` / `rustc` / `pnpm` / `node` 等外部可执行文件时，必须用 `Start-Process -NoNewWindow -Wait -PassThru` 包装调用，**禁止**直接用 `& cargo build` 或 `cargo build` 调用。原因：PowerShell 在 `$ErrorActionPreference = 'Stop'` 模式下，外部工具的 stderr 输出（即使只是 cargo 的进度/警告信息，如 `warning: unused variable`）会被 PowerShell 当作未捕获的错误流终止脚本；或被静默吞掉导致错误信息丢失。`Start-Process -NoNewWindow` 让外部工具在当前控制台窗口运行（输出直接继承当前 stdout/stderr），`-Wait` 等待退出，`-PassThru` 返回进程对象用于检查 `ExitCode`。评审时确认所有外部工具调用都用 `Start-Process` 模式。
- **Suggested fix**:

```powershell
$ErrorActionPreference = 'Stop'

# 错误 1：直接 & 调用，stderr 会触发 ErrorActionPreference=Stop 终止脚本
& cargo build                    # ❌ cargo 的 stderr 输出会终止脚本
& cargo tauri build --debug      # ❌ 同上

# 错误 2：直接命令调用（无 & 前缀），同样问题
cargo build                       # ❌ PowerShell 仍按外部命令解析，stderr 问题不变

# 正确：用 Start-Process 包装
$proc = Start-Process -FilePath "cargo" -ArgumentList "build" -NoNewWindow -Wait -PassThru
if ($proc.ExitCode -ne 0) {
    throw "cargo build 失败，退出码 $($proc.ExitCode)"
}

# 复杂参数场景：用 -ArgumentList 数组
$proc = Start-Process -FilePath "cargo" `
    -ArgumentList @("tauri", "build", "--debug") `
    -NoNewWindow -Wait -PassThru
if ($proc.ExitCode -ne 0) {
    throw "cargo tauri build 失败，退出码 $($proc.ExitCode)"
}
```

### BR-046: 禁止用 `2>&1 | Out-Host` 合并 stderr 与 stdout

- **Severity**: critical
- **Description**: 在 PowerShell 中合并外部工具的 stderr 与 stdout（`& cargo build 2>&1 | Out-Host`）会让 stderr 失去错误语义——所有 stderr 输出被当作普通文本显示，无法区分 cargo 的警告（`warning:`）与致命错误（`error:`），错误定位时须从混在一起的输出中肉眼筛选。更严重的是，`2>&1` 在 PowerShell 中会将 stderr 转换为 `ErrorRecord` 对象流，在 `$ErrorActionPreference = 'Stop'` 模式下仍可能触发脚本终止，行为不可预测。必须用 `Start-Process -RedirectStandardError` 将 stderr 单独重定向到文件，便于后续错误定位。
- **Suggested fix**:

```powershell
$ErrorActionPreference = 'Stop'

# 错误 1：用 2>&1 | Out-Host 合并流，stderr 错误语义丢失
& cargo build 2>&1 | Out-Host         # ❌ stderr 被合并为普通输出，错误难定位

# 错误 2：用 2>&1 重定向到文件（仍会被 ErrorActionPreference=Stop 拦截）
& cargo build 2>&1 | Out-File build.log   # ❌ PowerShell ErrorRecord 流问题不变

# 正确：用 Start-Process 分别重定向 stdout 与 stderr
$stdoutFile = [System.IO.Path]::GetTempFileName()
$stderrFile = [System.IO.Path]::GetTempFileName()
$proc = Start-Process -FilePath "cargo" `
    -ArgumentList "build" `
    -NoNewWindow -Wait -PassThru `
    -RedirectStandardOutput $stdoutFile `
    -RedirectStandardError $stderrFile
if ($proc.ExitCode -ne 0) {
    $stderrContent = Get-Content $stderrFile -Raw
    Write-Host "=== stdout ===" -ForegroundColor Cyan
    Get-Content $stdoutFile | ForEach-Object { Write-Host $_ }
    Write-Host "=== stderr ===" -ForegroundColor Red
    Write-Host $stderrContent
    Remove-Item $stdoutFile, $stderrFile -Force
    throw "cargo build 失败（退出码 $($proc.ExitCode)），详见上方 stderr 输出"
}
Remove-Item $stdoutFile, $stderrFile -Force
```

### BR-047: `$ErrorActionPreference = 'Stop'` 模式下必须用 `Start-Process` 避免外部工具 stderr 误报

- **Severity**: suggestion
- **Description**: PowerShell 脚本若在文件顶部声明 `$ErrorActionPreference = 'Stop'`（让 cmdlet 错误立即终止脚本），则调用所有外部可执行文件（cargo / rustc / pnpm / node / tsc 等）时**必须**用 `Start-Process` 包装。`ErrorActionPreference = 'Stop'` 影响 PowerShell 处理 `ErrorRecord` 流的方式——外部工具的 stderr 输出会被转换为 `ErrorRecord`，触发 Stop 行为让脚本提前终止。若脚本未声明 `$ErrorActionPreference`（默认为 `Continue`），直接 `& cargo` 调用不会立即终止，但仍会污染 PowerShell 的 `$Error` 集合，影响后续错误处理逻辑。建议：所有 PowerShell 脚本统一用 `$ErrorActionPreference = 'Stop'` + `Start-Process` 模式，避免双重标准。
- **Suggested fix**:

```powershell
# 错误：声明 Stop 但仍用 & 调用
$ErrorActionPreference = 'Stop'
& cargo build                    # ❌ stderr 触发 Stop，脚本提前终止
Write-Host "构建完成"            # 不会执行到这里

# 错误：未声明 ErrorActionPreference（默认 Continue），stderr 污染 $Error 集合
# 脚本顶部无 $ErrorActionPreference 声明
& cargo build                    # ⚠️ 不终止，但 $Error 集合被污染
if ($LASTEXITCODE -ne 0) {       # 须用 $LASTEXITCODE 而非 $?
    throw "cargo build 失败"
}

# 正确：声明 Stop + 用 Start-Process 包装
$ErrorActionPreference = 'Stop'

function Invoke-ExternalTool {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [string]$WorkingDirectory
    )
    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()
    try {
        $params = @{
            FilePath               = $FilePath
            ArgumentList           = $ArgumentList
            NoNewWindow            = $true
            Wait                   = $true
            PassThru               = $true
            RedirectStandardOutput = $stdoutFile
            RedirectStandardError  = $stderrFile
        }
        if ($WorkingDirectory) { $params.WorkingDirectory = $WorkingDirectory }
        $proc = Start-Process @params
        if ($proc.ExitCode -ne 0) {
            $stderrContent = Get-Content $stderrFile -Raw
            Write-Host "工具 $FilePath 失败，stderr:" -ForegroundColor Red
            Write-Host $stderrContent
            throw "$FilePath 退出码 $($proc.ExitCode)"
        }
    } finally {
        Remove-Item $stdoutFile, $stderrFile -Force -ErrorAction SilentlyContinue
    }
}

# 调用示例
Invoke-ExternalTool -FilePath "cargo" -ArgumentList @("build")
Invoke-ExternalTool -FilePath "cargo" -ArgumentList @("tauri", "build", "--debug")
Invoke-ExternalTool -FilePath "pnpm" -ArgumentList @("--filter", "@karpathy-wiki/web", "build")
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `powershell_stderr.enabled` | `true` | 是否启用本组规则（BR-045~047） |
| `powershell_stderr.severity_br045` | `critical` | BR-045 直接 `&` 调用违规严重级别 |
| `powershell_stderr.severity_br046` | `critical` | BR-046 `2>&1` 合并流违规严重级别 |
| `powershell_stderr.severity_br047` | `suggestion` | BR-047 Stop 模式下未用 Start-Process 违规严重级别 |
| `powershell_stderr.script_glob_pattern` | `**/*.ps1` | 扫描的 PowerShell 脚本文件 glob 模式 |
| `powershell_stderr.start_process_required_commands` | `cargo,rustc,pnpm,npm,node,tsc,tsx,git,go,python,py,java,dotnet` | 必须用 Start-Process 包装的外部工具列表（逗号分隔） |
| `powershell_stderr.forbidden_invoke_pattern` | `&\s*\b(cargo|rustc|pnpm|npm|node|tsc|tsx|git|go|python|py|java|dotnet)\b` | 禁用的 `& <tool>` 直接调用匹配模式（正则） |
| `powershell_stderr.forbidden_redirect_pattern` | `2>&1.*\|\s*Out-Host` | 禁用的 stderr 合并模式（正则，匹配 `2>&1 | Out-Host`） |
| `powershell_stderr.required_start_process_params` | `-NoNewWindow,-Wait,-PassThru` | `Start-Process` 必备参数列表（逗号分隔） |
| `powershell_stderr.error_action_preference_pattern` | `\$ErrorActionPreference\s*=\s*['"]Stop['"]` | `$ErrorActionPreference = 'Stop'` 声明匹配模式（正则） |
| `powershell_stderr.exit_code_check_pattern` | `ExitCode|LASTEXITCODE` | 退出码检查字段匹配模式（正则） |
| `powershell_stderr.recommended_redirect_params` | `-RedirectStandardOutput,-RedirectStandardError` | 推荐的 stderr/stdout 重定向参数（逗号分隔） |

## 检查方式

1. 用 Glob 检索 `powershell_stderr.script_glob_pattern` 下所有 `.ps1` 文件。
2. 对每个脚本，用 Read 读取完整内容。
3. **BR-045 检查**：
   - 用 Grep 检索 `powershell_stderr.forbidden_invoke_pattern`（如 `&\s*cargo`）：
     - 命中 → BR-045 违规（直接用 `&` 调用外部工具）
   - 用 Grep 检索 `powershell_stderr.start_process_required_commands` 中每个工具名（如 `^cargo\s` / `^pnpm\s`，行首直接调用无 `&` 前缀的命令）：
     - 命中 → BR-045 违规（直接命令调用，未用 Start-Process）
   - 用 Grep 检索 `Start-Process`：
     - 命中 → 检查是否包含 `powershell_stderr.required_start_process_params` 中的所有必备参数（`-NoNewWindow` / `-Wait` / `-PassThru`），缺失任一 → BR-045 违规
4. **BR-046 检查**：
   - 用 Grep 检索 `powershell_stderr.forbidden_redirect_pattern`（如 `2>&1.*\|\s*Out-Host`）：
     - 命中 → BR-046 违规（用 `2>&1 | Out-Host` 合并 stderr 与 stdout）
   - 用 Grep 检索 `2>&1.*Out-File` / `2>&1.*Tee-Object`：
     - 命中 → BR-046 违规（同类合并流问题）
5. **BR-047 检查**：
   - 用 Grep 检索 `powershell_stderr.error_action_preference_pattern`（如 `\$ErrorActionPreference\s*=\s*['"]Stop['"]`）：
     - 命中 → 脚本声明了 Stop 模式，所有外部工具调用必须用 Start-Process
     - 进一步检查 BR-045 命中的违规项，在 Stop 模式下违规严重级别从 `critical` 提升至 `critical`（已是最高，但额外标注"Stop 模式下违规更严重"）
   - 未命中 → 脚本未声明 Stop 模式，BR-045 / BR-046 仍按原严重级别检查；同时给出 suggestion 级建议：声明 `$ErrorActionPreference = 'Stop'` + 用 `Start-Process` 统一模式
6. 用 Grep 检索 `ExitCode` / `$LASTEXITCODE`：
   - 命中 → 退出码检查存在
   - 未命中但脚本调用外部工具 → suggestion 级建议（未检查退出码，构建失败时无法定位）

## 正确示例

```powershell
# tauri-build-debug.ps1 —— 完整合规脚本
$ErrorActionPreference = 'Stop'

# 通用工具调用函数：用 Start-Process 包装外部工具
function Invoke-ExternalTool {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [string]$WorkingDirectory
    )
    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()
    try {
        $params = @{
            FilePath               = $FilePath
            ArgumentList           = $ArgumentList
            NoNewWindow            = $true
            Wait                   = $true
            PassThru               = $true
            RedirectStandardOutput = $stdoutFile
            RedirectStandardError  = $stderrFile
        }
        if ($WorkingDirectory) { $params.WorkingDirectory = $WorkingDirectory }
        $proc = Start-Process @params
        # 显示工具输出
        Get-Content $stdoutFile | ForEach-Object { Write-Host $_ }
        if ($proc.ExitCode -ne 0) {
            $stderrContent = Get-Content $stderrFile -Raw
            Write-Host "工具 $FilePath 失败，stderr:" -ForegroundColor Red
            Write-Host $stderrContent
            throw "$FilePath 退出码 $($proc.ExitCode)"
        }
    } finally {
        Remove-Item $stdoutFile, $stderrFile -Force -ErrorAction SilentlyContinue
    }
}

# 磁盘空间预检查（PSDrive 是 PowerShell cmdlet，可直接调用）
$requiredGb = 3
$drive = (Get-Item $PSScriptRoot).PSDrive
$freeGb = [math]::Round($drive.Free / 1GB, 2)
if ($freeGb -lt $requiredGb) {
    throw "磁盘空间不足：当前 $freeGb GB，至少需要 $requiredGb GB"
}

# 清理旧产物（PowerShell cmdlet，不涉及外部工具 stderr 问题）
$publicDir = "services/api/public"
if (Test-Path $publicDir) {
    Remove-Item -Path "$publicDir/*" -Recurse -Force
}

# 构建 SPA（用 Start-Process 包装 pnpm）
Invoke-ExternalTool -FilePath "pnpm" `
    -ArgumentList @("--filter", "@karpathy-wiki/web", "build")

# 验证 SPA 产物
$indexHtml = Join-Path $publicDir "index.html"
if (-not (Test-Path $indexHtml)) {
    throw "SPA 构建失败：$indexHtml 不存在"
}

# 构建 Tauri（用 Start-Process 包装 cargo）
Invoke-ExternalTool -FilePath "cargo" `
    -ArgumentList @("tauri", "build", "--debug")

Write-Host "Tauri 桌面应用构建完成" -ForegroundColor Green
```

## 错误示例

```powershell
# 错误 1：直接 & 调用（BR-045 违规）
$ErrorActionPreference = 'Stop'
& cargo build                    # ❌ stderr 触发 Stop 终止脚本
& cargo tauri build --debug     # ❌ 同上

# 错误 2：直接命令调用无 & 前缀（BR-045 违规）
cargo build                       # ❌ 仍按外部命令解析，stderr 问题不变
pnpm --filter @karpathy-wiki/web build   # ❌ 同上

# 错误 3：用 2>&1 | Out-Host 合并流（BR-046 违规）
& cargo build 2>&1 | Out-Host    # ❌ stderr 错误语义丢失
& cargo tauri build --debug 2>&1 | Out-File build.log  # ❌ 同类问题

# 错误 4：声明 Stop 但仍用 & 调用（BR-047 违规）
$ErrorActionPreference = 'Stop'
& cargo build                    # ❌ Stop 模式下 stderr 必触发终止，脚本永远跑不到下一行
Write-Host "构建完成"            # 不会执行

# 错误 5：Start-Process 缺少必备参数（BR-045 违规）
$proc = Start-Process -FilePath "cargo" -ArgumentList "build"   # ❌ 缺 -NoNewWindow / -Wait / -PassThru
# Start-Process 默认在新窗口启动且不等待，无法检查 ExitCode

# 错误 6：未检查退出码
$ErrorActionPreference = 'Stop'
$proc = Start-Process -FilePath "cargo" -ArgumentList "build" -NoNewWindow -Wait -PassThru
# ❌ 缺 if ($proc.ExitCode -ne 0) { throw ... }，构建失败仍继续执行后续步骤
Write-Host "构建完成"            # 即使 cargo 失败也会打印
```

## 适配新项目

- **不同工具链项目**：`start_process_required_commands` 按项目实际使用的外部工具扩展（如 Go 项目追加 `go` / `golangci-lint`；Python 项目追加 `python` / `pip` / `poetry`；Java 项目追加 `mvn` / `gradle` / `java`）。
- **Bash / Zsh 项目**：本规则仅适用于 PowerShell 脚本，Bash 中 `cargo build 2>&1` 是合法用法（bash 的 stderr 重定向语义与 PowerShell 不同），无需检查；将 `script_glob_pattern` 设为 `**/*.ps1` 即可仅扫描 PowerShell 脚本。
- **CI/CD 脚本项目**：CI 配置文件（如 `.github/workflows/*.yml`）中的 PowerShell 步骤同样适用本规则，但需先提取 YAML 中的 `run:` 块内容再扫描。
- **跨平台脚本项目**：若项目同时有 `.ps1`（Windows）与 `.sh`（Linux/macOS）脚本，建议在 `.ps1` 中用 `Start-Process` 模式（本规则），在 `.sh` 中用 `set -e` + 直接调用（bash 语义不同）。
- **PowerShell Core 7+ 项目**：PowerShell 7+ 改进了 stderr 处理（`$PSNativeCommandUseErrorActionPreference` 变量），但默认仍按 5.1 行为；建议统一用 `Start-Process` 模式以兼容 5.1 与 7+。
