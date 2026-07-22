# Async 可靠性测试参考

> 本文档提供 async/await + IPC 场景的可靠性测试方法，对应 wiki-code-dev 的 CODING-021~025 规则。
> 所有测试参数从 `config.yaml` 的 `async_reliability_tests` 节读取，不在代码中硬编码。

## 1. 测试目标

验证 async 代码在以下场景下的可靠性：
- IPC 调用超时后能否降级而非崩溃
- 事件循环阻塞时心跳是否仍能更新状态文件
- 超时后是否有兜底数据可供流程继续
- 多层超时配置是否合理

## 2. 测试方法

### 2.1 静态检查（grep 模式）

**适用规则**：CODING-021、CODING-022、CODING-023、CODING-024

**执行方式**：
```powershell
# CODING-021：检查 async 调用是否有超时保护
Select-String -Path "scripts\*.py" -Pattern "await\s+\w+\." | Where-Object {
    $_.Line -notmatch "asyncio\.sleep|Promise\.resolve" -and
    $_.Line -notmatch "asyncio\.wait_for|Promise\.race"
}

# CODING-022：检查心跳是否使用 asyncio.Task（违规）
Select-String -Path "scripts\*.py" -Pattern "asyncio\.create_task|asyncio\.Task" |
    Where-Object { $_.Line -match "heartbeat|心跳|status" }

# CODING-024：检查 wait_for 超时后是否有兜底数据
Select-String -Path "scripts\*.py" -Pattern "asyncio\.wait_for" -Context 0,5 |
    Where-Object { $_.Context.PostContext -match "raise|pass" -and
                   $_.Context.PostContext -notmatch "best_holder|fallback|last_known" }
```

**判断标准**：
- CODING-021：有未包裹的 await 调用 → 🔴 critical
- CODING-022：心跳使用 asyncio.Task → 🔴 critical
- CODING-024：超时后 raise/pass 而无兜底数据 → 🟡 warning

### 2.2 运行时监控

**适用规则**：CODING-023

**执行方式**：
1. 启动子进程（如 browser_login.py）
2. 监控状态文件 `ts` 字段更新间隔
3. 记录每次 ts 更新的时间戳
4. 计算相邻更新的间隔
5. 若间隔 > `max_gap_sec`（默认 10s）→ 测试失败

**PowerShell 监控脚本模板**（参数从 config.yaml 读取）：
```powershell
# 以下参数应从 config.yaml 的 async_reliability_tests.runtime_verification 读取
$statusFilePattern = "C:\Users\hspcadmin\AppData\Local\Temp\xh_browser_login\browser_login_*.json"
$monitorDuration = 90  # monitor_duration_sec
$maxGap = 10  # max_gap_sec
$startTime = Get-Date
$lastTs = 0

while ((Get-Date) - $startTime -lt (New-TimeSpan -Seconds $monitorDuration)) {
    $file = Get-ChildItem $statusFilePattern -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($file) {
        $content = Get-Content $file.FullName -Raw | ConvertFrom-Json
        if ($content.ts -ne $lastTs) {
            $gap = $content.ts - $lastTs
            if ($lastTs -gt 0 -and $gap -gt $maxGap) {
                Write-Output "FAIL: ts update gap ${gap}s exceeds threshold ${maxGap}s"
                exit 1
            }
            $lastTs = $content.ts
        }
    }
    Start-Sleep -Seconds 1
}
Write-Output "PASS: ts field updated within ${monitorDuration}s"
```

### 2.3 模拟阻塞测试

**适用规则**：CODING-022、CODING-023

**执行方式**：
1. 在测试环境中模拟 IPC 阻塞（如 mock Playwright context.cookies() 返回永久挂起的 future）
2. 监控状态文件 ts 字段更新
3. 确认心跳线程仍能更新 ts（即使业务循环卡住）

**Python 测试模板**：
```python
import asyncio
import threading
import time
import json
from pathlib import Path

async def mock_blocking_call():
    """Simulate a permanently hung IPC call."""
    await asyncio.Future()  # Never completes

def test_heartbeat_during_blocking():
    """Test that heartbeat still works when event loop is blocked."""
    status_file = Path("test_status.json")
    stop_event = threading.Event()
    
    def heartbeat_thread():
        while not stop_event.is_set():
            time.sleep(0.1)
            status_file.write_text(json.dumps({"ts": time.time()}))
    
    thread = threading.Thread(target=heartbeat_thread, daemon=True)
    thread.start()
    
    # Simulate business loop being blocked
    async def blocking_business():
        try:
            await asyncio.wait_for(mock_blocking_call(), timeout=2.0)
        except asyncio.TimeoutError:
            pass
    
    asyncio.run(blocking_business())
    
    # Verify heartbeat thread updated ts during business block
    content = json.loads(status_file.read_text())
    assert time.time() - content.ts < 1.0, "Heartbeat thread did not update ts within 1s"
    
    stop_event.set()
    thread.join(timeout=1)
    status_file.unlink()
```

## 3. 测试场景覆盖矩阵

| 规则 ID | 静态检查 | 运行时监控 | 模拟阻塞 | 单元测试 |
|---------|---------|-----------|---------|---------|
| CODING-021 | ✅ grep await | - | - | - |
| CODING-022 | ✅ grep asyncio.Task | - | ✅ mock blocking | ✅ test_heartbeat_during_blocking |
| CODING-023 | ✅ grep status writer | ✅ monitor ts | ✅ mock blocking | - |
| CODING-024 | ✅ grep wait_for except | - | - | ✅ test_fallback_data |
| CODING-025 | - | - | - | ✅ test_multi_layer_timeout |

## 4. 测试报告格式

Async 可靠性测试结果必须包含以下字段：

```
## Async Reliability Test Report
- CODING-021 Timeout Protection: PASS/FAIL (N violations)
- CODING-022 Heartbeat Thread Impl: PASS/FAIL (asyncio.Task violation)
- CODING-023 Status File Update Independence: PASS/FAIL (max ts gap Xs)
- CODING-024 Fallback Data: PASS/FAIL (N timeout without fallback)
- CODING-025 Multi-layer Timeout: PASS/FAIL (single layer only)
```

## 5. 适用场景

- ✅ Python asyncio + Playwright projects
- ✅ Node.js + Playwright projects
- ✅ Sub-process communication via status file
- ✅ Projects using SSE streaming
- ❌ Pure synchronous code projects
- ❌ Simple web projects without IPC calls
