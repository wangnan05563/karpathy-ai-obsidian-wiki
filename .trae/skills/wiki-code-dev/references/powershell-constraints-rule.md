# PowerShell Constraints Rule

## 触发关键词

PowerShell, ps1, &&, $pid, $PWD, $HOME, cmd /c, Get-NetTCPConnection, Stop-Process, here-string, cwd, RunCommand, 端口占用

## 规则

### PS-1：禁用 `&&` 命令分隔符

**严重级别**：critical

PowerShell 不支持 bash 的 `&&` 语法，使用 `&&` 会触发语法解析错误。多命令串接必须用 `command_separator` 指定的分隔符（默认 `;`）或换行。

**为什么**：PowerShell 把 `&&` 视为未识别 token，整条命令解析失败；而 `;` 是语句分隔符，无论前一命令成败都会执行下一条，符合大多数自动化场景。需要"前一条成功才执行下一条"时用 `if ($LASTEXITCODE -eq 0) { ... }`。

**错误示例**：
```powershell
# ❌ bash 语法，PowerShell 报错
npm run build && npm run test
```

**正确示例**：
```powershell
# ✅ 用 command_separator（默认 ;）
npm run build ; npm run test

# ✅ 需要短路语义时显式判断
npm run build
if ($LASTEXITCODE -eq 0) { npm run test }
```

### PS-2：禁用只读变量赋值

**严重级别**：critical

`readonly_vars` 列表中的变量（默认 `$pid`, `$PWD`, `$HOME`）为 PowerShell 内建只读变量，赋值会报 `Cannot overwrite variable` 错误。必须改用其他变量名。

**为什么**：`$pid` 是当前进程 PID，`$PWD` 是当前工作目录，`$HOME` 是用户主目录。覆盖会破坏 PowerShell 内部状态，赋值直接抛错阻断流程。

**错误示例**：
```powershell
# ❌ $pid 是只读变量
$pid = Get-NetTCPConnection -LocalPort 3000 | Select -Expand OwningProcess
```

**正确示例**：
```powershell
# ✅ 改用 $procId 等普通变量名
$procId = Get-NetTCPConnection -LocalPort 3000 | Select -Expand OwningProcess
Stop-Process -Id $procId -Force
```

### PS-3：禁用 `cmd /c` 调用

**严重级别**：critical

`blocked_commands` 列表中的命令（默认 `cmd /c`）会被安全策略或沙箱阻断。需要执行 cmd 内置命令时，改用 PowerShell 等价命令。

**为什么**：`cmd /c` 启动子 cmd.exe 进程，企业安全策略常将其判定为可疑子进程派生而阻断；且 cmd 与 PowerShell 字符串转义规则不同，混用易出错。

**错误示例**：
```powershell
# ❌ 被安全策略阻止
cmd /c "dir /b"
cmd /c "copy a.txt b.txt"
```

**正确示例**：
```powershell
# ✅ PowerShell 原生命令
Get-ChildItem -Name
Copy-Item a.txt b.txt
```

### PS-4：`cd` 在子 shell 不生效，改用 `cwd` 参数

**严重级别**：critical

`RunCommand` 在独立子 shell 中执行命令，子 shell 中的 `cd` 不会影响后续命令的工作目录。必须通过 `RunCommand` 的 `cwd_param`（默认 `cwd`）参数指定工作目录。

**为什么**：每条 `RunCommand` 调用都是独立进程，`cd` 仅改变当前进程的 CWD，进程结束即失效。下一条调用又回到默认 CWD，相对路径解析错误。

**错误示例**：
```powershell
# ❌ cd 不生效，下一条命令仍在原目录
cd d:\project ; npm run build
```

**正确示例**：
```
# ✅ 通过 RunCommand 的 cwd 参数指定
RunCommand(
  command="npm run build",
  cwd="d:\project"
)
```

### PS-5：单引号 here-string 不进行转义

**严重级别**：suggestion

PowerShell 单引号 here-string `@'...'@` 内的所有字符均为字面量，包括 `` `n ``、`` `t `` 等转义符。需要换行符时用 `.Replace()` 或双引号 here-string `@"..."@`。

**为什么**：单引号 here-string 设计目的就是"原样保留"，常见于写脚本块、配置文件模板。误把 `` `n `` 当换行会导致文件中出现字面字符串 `` `n `` 而非 LF。

**错误示例**：
```powershell
# ❌ 输出 "line1`nline2"，无换行
$content = @'
line1`nline2
'@
[System.IO.File]::WriteAllText("out.txt", $content)
```

**正确示例**：
```powershell
# ✅ 用 .Replace() 修复
$content = @'
line1__NL__line2
'@.Replace("__NL__", "`r`n")

# ✅ 或用双引号 here-string（注意变量会被展开）
$content = @"
line1`nline2
"@
```

### PS-6：服务生命周期管理必须遵循固定流程

**严重级别**：suggestion

启动前后端服务、停止旧进程、验证端口监听必须按固定流程，避免端口占用或僵尸进程。详见下方"服务生命周期管理模板"。

### PS-6.1：清理占用端口的旧进程必须 `Stop-Process -Force` + `try/catch`，禁止裸 `taskkill`

**严重级别**：critical

启动/重启脚本在 `[1/4]` 清理旧进程阶段，必须用 `Stop-Process -Id $procId -Force` 且**包裹 `try/catch`** 使清理成为非致命步骤；**禁止以裸 `taskkill` 作为清理主键**。

**为什么**：
- 在 `$ErrorActionPreference = "Stop"` 下，`taskkill` 的 stderr（如"错误: 无法终止 PID X (属于 PID Y 子进程)的进程" / "进程已退出"）会被 PowerShell 包装为 `NativeCommandError` 并**中止整个脚本**（即本次会话报的 `[ERROR] Start failed`）。
- `taskkill /F /T /PID` 对"属于其他进程子进程"的 PID 会**直接拒绝**，无法清理。
- `Stop-Process -Force` 无此限制；配合 `try/catch` 后，进程已退出/被回收时静默跳过，端口释放交由后续 `Wait-PortReady`（模板 C）探测确认——清理失败绝不应阻断启动。

**残留进程兜底**：多个 `tsx watch` / `vite` 竞争同一端口时，均未成功 `LISTENING`，端口扫描（`Get-NetTCPConnection`）返回空但进程仍在运行。此时用 `Get-CimInstance Win32_Process` 按命令行匹配（`*dev:api*` / `*tsx*src/index.ts` / `*vite*bin/vite`）兜底清理；该路径仍用 `taskkill /F /T` 但**必须 `2>&1 | Out-Null` + `try/catch` + 仅以 `$LASTEXITCODE -eq 0` 判定成功**，绝不让其 stderr 冒泡中止脚本。

**错误示例**：
```powershell
# ❌ 裸 taskkill 主键 + 无 try/catch：stderr 在 $ErrorActionPreference='Stop' 下中止脚本
taskkill /F /T /PID $procId
```

**正确示例**：
```powershell
# ✅ Stop-Process -Force + try/catch，清理非致命
try { Stop-Process -Id $procId -Force -ErrorAction Stop } catch { }
# 残留兜底（命令行匹配），taskkill 仅作兜底且吞掉 stderr
foreach ($p in $strayProcs) {
  try { taskkill /F /T /PID $p.ProcessId 2>&1 | Out-Null } catch { }
  if ($LASTEXITCODE -eq 0) { Write-Log "已清理残留进程 (PID $($p.ProcessId))" }
}
```

**适用**：Windows PowerShell 服务启动/重启脚本清理占用端口的进程。
**不适用**：Bash / Zsh 启动脚本（stderr 不触发终止错误，裸 `kill`/`fuser` 可接受）；纯单命令无清理需求的脚本。

## 服务生命周期管理模板

### 模板 A：停止占用端口的旧进程

```powershell
# $Port 值由调用方从 config.required_ports 读取后传入（不在模板内硬编码端口号）
param([int]$Port)

$conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($conns) {
  $procId = $conns.OwningProcess | Select-Object -First 1
  Write-Host "端口 $Port 被进程 $procId 占用，停止中..."
  # 清理旧进程必须是「非致命」步骤：进程可能已退出/被回收，Stop-Process 在
  # $ErrorActionPreference='Stop' 下仍可能抛错，故用 try/catch 包裹，失败静默跳过，
  # 端口释放与否交由后续 Wait-PortReady 探测确认（见 模板 C）。
  # 禁止用裸 taskkill：taskkill 的 stderr（"进程已退出/属于子进程"）在
  # $ErrorActionPreference='Stop' 下被包装为 NativeCommandError 中止整个脚本；
  # 且 taskkill /F /T 对"属于其他进程子进程"的 PID 直接拒绝。
  try { Stop-Process -Id $procId -Force -ErrorAction Stop } catch { }
  # 等待端口释放
  Start-Sleep -Seconds 1
} else {
  Write-Host "端口 $Port 空闲"
}
```

### 模板 B：启动服务（非阻塞）

`dev:api` / `dev:web` 必须以非阻塞方式启动，否则会卡住当前会话。通过 `RunCommand` 的 `blocking: false` 配合 `command_type: "web_server"` 或 `"long_running_process"`。

```
# 后端 API 服务
RunCommand(
  command="npm run dev:api",
  blocking=false,
  command_type="web_server",
  cwd="<project-root>"
)

# 前端 Web 服务
RunCommand(
  command="npm run dev:web",
  blocking=false,
  command_type="web_server",
  cwd="<project-root>"
)
```

### 模板 C：验证端口监听

```powershell
# 等待并验证端口监听
# $TimeoutSec 默认值来自 config.startup_timeout_ms（换算为秒）
function Wait-PortListening {
  param(
    [int]$Port,
    [int]$TimeoutSec = 30  # 调用方可从 config.startup_timeout_ms 读取并换算传入
  )
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  while ((Get-Date) -lt $deadline) {
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
      Write-Host "端口 $Port 已监听 (PID: $($conn.OwningProcess))"
      return $true
    }
    Start-Sleep -Milliseconds 500
  }
  Write-Warning "等待端口 $Port 监听超时"
  return $false
}

# $ports 值由调用方从 config.required_ports 读取后传入（不在模板内硬编码端口号）
# foreach 遍历所有所需端口，统一验证监听状态
foreach ($p in $ports) {
  Wait-PortListening -Port $p
}
```

### 模板 D：完整启动闭环

```powershell
# $ports 值由调用方从 config.required_ports 读取后传入（不在模板内硬编码端口号）
# 示例：$ports = @(3000, 5173)  # 实际值来自 config

# 1. 停止旧进程（模板 A）
foreach ($p in $ports) {
  $c = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
  if ($c) { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue }
}

# 2. 启动服务（模板 B，通过 RunCommand blocking=false）
#    RunCommand npm run dev:api  (cwd=project, blocking=false, command_type=web_server)
#    RunCommand npm run dev:web  (cwd=project, blocking=false, command_type=web_server)

# 3. 验证端口监听（模板 C，遍历 config.required_ports 所有端口）
foreach ($p in $ports) {
  Wait-PortListening -Port $p
}
```

## 禁用语法速查

| 禁用 | 替代 | 说明 |
|------|------|------|
| `&&` | `;` 或 `if ($LASTEXITCODE -eq 0)` | 来自 config `command_separator` |
| `||` | `if ($LASTEXITCODE -ne 0)` | 短路失败语义 |
| `$pid = ...` | `$procId = ...` | 来自 config `readonly_vars` |
| `$PWD = ...` | `$workDir = ...` | 来自 config `readonly_vars` |
| `$HOME = ...` | `$homeDir = ...` | 来自 config `readonly_vars` |
| `cmd /c "..."` | PowerShell 原生命令 | 来自 config `blocked_commands` |
| `cd path; cmd` | `RunCommand(cwd=path)` | 来自 config `cwd_param` |
| 单引号 here-string 中 `` `n `` | `.Replace()` 或双引号 here-string | 转义陷阱 |

## 适用场景

- Windows PowerShell 自动化脚本开发
- RunCommand 工具调用前后端服务
- 服务端口管理（启动/停止/验证）
- 多命令串接的构建/测试脚本
- 与 bash 脚本移植到 PowerShell 的场景

## 不适用场景

- Linux/macOS bash/zsh 环境（语法不同）
- PowerShell Core on Linux（部分命令行为差异）
- cmd.exe 批处理（语法完全不同，参考 bat 脚本约束段）
- 单条原子命令（无串接需求）

## 检查清单

- [ ] 是否使用 `;` 而非 `&&` 串接命令
- [ ] 是否避免给 `$pid` / `$PWD` / `$HOME` 等只读变量赋值
- [ ] 是否避免 `cmd /c` 调用
- [ ] 是否通过 `cwd` 参数指定工作目录而非依赖 `cd`
- [ ] 单引号 here-string 中的换行是否用 `.Replace()` 修复
- [ ] 启动服务前是否停止占用端口的旧进程
- [ ] 启动服务是否用非阻塞模式
- [ ] 启动后是否验证端口监听状态
