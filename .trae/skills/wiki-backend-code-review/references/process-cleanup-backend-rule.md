# Rule Catalog — PowerShell 端口清理安全 (BR-093)

后端审查条目，对应通用编码规范 `CODING-PS-PROCESS-CLEANUP`（wiki-code-dev references/powershell-constraints-rule.md PS-6.1）。服务启动 / 重启脚本（`scripts/start-service.ps1` 等）在清理占用端口的旧进程阶段，必须以 `Stop-Process -Force` + `try/catch` 使清理成为非致命步骤，且**禁止以裸 `taskkill` 作为清理主键**——其 stderr 在 `$ErrorActionPreference='Stop'` 下会被包装为 `NativeCommandError` 中止整个脚本（即 `[ERROR] Start failed`）。

> 复盘来源：启动脚本 `[1/4]` 清理旧进程阶段使用裸 `taskkill /F /T /PID`，在 `$ErrorActionPreference='Stop'` 下 `taskkill` 的 stderr（"错误: 无法终止 PID 8052 (属于 PID 32556 子进程)的进程"）被 PowerShell 包装为 `NativeCommandError`，导致整个启动脚本中止、服务起不来。修正：端口清理改 `Stop-Process -Id $procId -Force` 并 `try/catch` 包裹（清理非致命），残留进程用 `Get-CimInstance` 命令行匹配兜底（该路径仍用 `taskkill` 但 `2>&1 | Out-Null` + `try/catch` 吞 stderr，仅以 `$LASTEXITCODE` 判定）。

## Scope

- Covers: Windows PowerShell 服务启动 / 重启脚本中"清理占用端口旧进程 / 残留 tsx/vite 进程"的逻辑（`scripts/*.ps1`）。
- Does NOT cover: Bash / Zsh 启动脚本（`stderr` 不触发终止错误，裸 `kill`/`fuser` 可接受）；纯单命令无清理需求的脚本；已成功的进程终止（非清理主键场景）。

## Rules

### BR-093-1: 端口清理主键须 `Stop-Process -Force` + `try/catch`（非致命）

Category: 后端 / 服务生命周期 / PowerShell
Severity: critical

#### Description

清理占用端口的旧进程必须以 `Stop-Process -Id $procId -Force` 为清理主键，且**包裹 `try/catch`** 使清理成为非致命步骤。进程可能已退出 / 被回收，`Stop-Process` 在 `$ErrorActionPreference='Stop'` 下仍可能抛错，捕获后静默跳过；端口释放与否交由后续 `Wait-PortReady` 探测确认——清理失败**绝不应**阻断启动。

#### Suggested Fix

```powershell
# ✅ Stop-Process -Force + try/catch，清理非致命
$apiPids = Get-PidOnPort -Port $apiPort
foreach ($procId in $apiPids) {
    try { Stop-Process -Id $procId -Force -ErrorAction Stop } catch { }
    Write-Log "已清理 API 端口 $apiPort 上的进程 (PID $procId)" -Level OK -Step "1/4"
}
```

### BR-093-2: 禁止裸 `taskkill` 作端口清理主键

Category: 后端 / 服务生命周期 / PowerShell
Severity: critical

#### Description

**禁止以裸 `taskkill` 作为端口清理主键**：在 `$ErrorActionPreference='Stop'` 下，`taskkill` 的 stderr（"无法终止 PID X (属于 PID Y 子进程)" / "进程已退出"）会被包装为 `NativeCommandError` 中止整个脚本；且 `taskkill /F /T` 对"属于其他进程子进程"的 PID 直接拒绝。残留进程兜底清理（命令行匹配 `tsx`/`vite`）允许使用 `taskkill`，但须 `2>&1 | Out-Null` + `try/catch` 吞掉 stderr，仅以 `$LASTEXITCODE -eq 0` 判定成功。

#### Suggested Fix

```powershell
# ❌ 裸 taskkill 主键 + 无 try/catch：stderr 在 $ErrorActionPreference='Stop' 下中止脚本
taskkill /F /T /PID $procId

# ✅ 残留兜底允许 taskkill，但须吞 stderr + try/catch + 仅以 LASTEXITCODE 判定
foreach ($p in $strayProcs) {
    try { taskkill /F /T /PID $p.ProcessId 2>&1 | Out-Null } catch { }
    if ($LASTEXITCODE -eq 0) {
        Write-Log "已清理残留进程 (PID $($p.ProcessId), $($p.Name))" -Level OK -Step "1/4"
    }
}
```

## Configuration Parameters

> 全部参数从 [config/review-config.md](../config/review-config.md) 的"PowerShell 端口清理安全审查参数（BR-093）"节读取，本规则文件不硬编码任何值。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `process_cleanup_safe.enabled` | `true` | 启用端口清理安全审查 |
| `process_cleanup_safe.scan_dirs` | `scripts` | 扫描的脚本目录 |
| `process_cleanup_safe.file_glob` | `*.ps1` | 扫描文件类型 |
| `process_cleanup_safe.forbidden_patterns` | `taskkill\s` | 禁止作为清理主键的裸 `taskkill` 模式 |
| `process_cleanup_safe.required_patterns` | `Stop-Process` | 端口清理主键须出现的进程终止命令 |
| `process_cleanup_safe.require_trycatch` | `true` | 进程终止命令须被 try/catch 包裹 |
| `process_cleanup_safe.severity` | `critical` | 裸 taskkill 主键 / 无 try/catch 导致启动脚本中止的违规级别 |
