# 后端 Async 可靠性审查规则

> 本规则对应 wiki-code-dev 的 CODING-021~025，提供后端代码审查的检查清单。
> 所有参数从 `config/review-config.md` 的"Async 可靠性审查参数"章节读取，禁止在规则文件硬编码。

## BR-ASYNC-01：async 调用必须设置超时

**严重级别**：🔴 critical

**检查内容**：后端代码中所有 `await` 调用（IPC、网络、文件 I/O、外部进程通信）必须被 `asyncio.wait_for`（Python）或 `Promise.race`（TypeScript）包裹，超时值从 `config.async_reliability.default_call_timeout_sec` 读取。

**违规模式**：
```python
# 违规：无超时保护
cookies = await context.cookies()
result = await fetch('https://api.example.com/data')
```

**合规模式**：
```python
try:
    cookies = await asyncio.wait_for(
        context.cookies(),
        timeout=config.async_reliability.default_call_timeout_sec,
    )
except asyncio.TimeoutError:
    cookies = best  # 降级到上次已知值
```

**检查方式**：
1. Grep `await\s+\w+\.` 在 async 函数中的调用
2. 排除 `config.async_reliability.timeout_whitelist` 中的白名单调用
3. 确认剩余调用是否被 `wait_for` / `Promise.race` 包裹

**误报场景**：
- `await asyncio.sleep(interval)`：sleep 本身有明确时长，无需额外超时
- `await Promise.resolve()`：立即返回，无阻塞风险

## BR-ASYNC-02：事件循环阻塞场景必须使用线程级心跳

**严重级别**：🔴 critical

**检查内容**：当后端代码使用 `config.async_reliability.blocking_risk_apis` 列表中的 API（Playwright、native addon 等）时，心跳/看门狗/状态更新逻辑必须用 `threading.Thread`（Python）或 `worker_threads`（Node.js）实现，禁止用 `asyncio.Task` / `Promise.then`。

**违规模式**：
```python
# 违规：asyncio.Task 在事件循环阻塞时无法调度
async def _heartbeat():
    while True:
        await asyncio.sleep(3)
        _emit_status("running")

heartbeat_task = asyncio.create_task(_heartbeat())
```

**合规模式**：
```python
import threading

_heartbeat_stop = threading.Event()

def _heartbeat_thread():
    while not _heartbeat_stop.is_set():
        time.sleep(config.async_reliability.heartbeat_interval_sec)
        if _heartbeat_stop.is_set():
            return
        _emit_status("running", "进行中...")

heartbeat = threading.Thread(target=_heartbeat_thread, daemon=True)
heartbeat.start()
try:
    result = await asyncio.wait_for(blocking_call(), timeout=30.0)
finally:
    _heartbeat_stop.set()
    heartbeat.join(timeout=config.async_reliability.thread_join_timeout_sec)
```

**检查方式**：
1. 识别代码中是否使用了 `config.async_reliability.blocking_risk_apis` 列表中的 API
2. 若使用，审查心跳/状态更新逻辑的实现方式
3. 确认是否使用 `threading.Thread` 或 `worker_threads`

**适用场景**：
- Python asyncio + Playwright/aiohttp 的后端
- Node.js + Playwright/native addon 的后端
- 子进程通过状态文件与主进程通信的架构

## BR-ASYNC-03：状态文件 ts 字段更新必须独立于业务事件循环

**严重级别**：🔴 critical

**检查内容**：子进程通过状态文件（JSON/YAML）与主进程通信时，状态文件的 `ts`（时间戳）字段更新逻辑必须满足以下任一条件：
1. 由独立线程写入（推荐，`status_file_update_strategy=thread`）
2. 由业务循环内的同步代码写入，且循环间隔 ≤ `config.async_reliability.heartbeat_max_interval_sec`

**违规模式**：
```python
# 违规：ts 更新依赖业务 async 循环，循环被阻塞时 ts 停止更新
async def main_loop():
    while True:
        await blocking_playwright_call()  # 卡住时 ts 无法更新
        _write_status_file({"ts": time.time()})
```

**合规模式**：
```python
# 合规：独立线程写 ts，与业务循环解耦
def _heartbeat_thread():
    while not _heartbeat_stop.is_set():
        time.sleep(config.async_reliability.heartbeat_interval_sec)
        _write_status_file({"ts": time.time(), "status": "running"})
```

**检查方式**：
1. Grep 状态文件写入函数（`_write_status`、`_emit_status`、`set_status`、`write_status_file`）
2. 确认调用方是否在独立线程中
3. 若在 async 循环中，确认循环间隔 ≤ `heartbeat_max_interval_sec`

**根因说明**：主进程通过 `ts` 字段判断子进程是否存活（如 90s 未更新则判定"无响应"）。若 `ts` 更新依赖业务 async 循环，当循环被 IPC 阻塞时 `ts` 停止更新，主进程误判子进程死亡。

## BR-ASYNC-04：async 调用超时必须提供兜底数据

**严重级别**：🟡 warning

**检查内容**：`asyncio.wait_for` / `Promise.race` 超时后的 except 分支必须有兜底数据赋值，禁止直接 raise 终止流程。兜底数据通过 `best_holder` 模式（可变容器）或闭包变量传递。

**违规模式**：
```python
# 违规：超时后无兜底，直接 raise
try:
    result = await asyncio.wait_for(blocking_call(), timeout=30.0)
except asyncio.TimeoutError:
    raise RuntimeError("超时")  # 流程终止，无法降级
```

**合规模式**：
```python
best_holder: list[dict] = []

async def _collect_with_fallback():
    best = []
    while True:
        try:
            current = await asyncio.wait_for(context.cookies(), timeout=5.0)
        except asyncio.TimeoutError:
            current = best
        if len(current) >= len(best):
            best = current
            best_holder.clear()
            best_holder.extend(best)

try:
    result = await asyncio.wait_for(_collect_with_fallback(), timeout=30.0)
except asyncio.TimeoutError:
    result = best_holder  # 兜底：最后已知数据
```

**检查方式**：
1. Grep `asyncio.wait_for` 和 `Promise.race` 调用
2. 审查 except 分支的处理逻辑
3. 确认是否有兜底数据赋值（`result = best_holder` / `result = last_known`）
4. 确认是否直接 raise 或 pass（违规）

## 审查流程集成

在 SKILL.md 的审查流程中，BR-ASYNC-01~04 应在以下时机执行：

1. **Pending-change review**：对修改的 .py / .ts 文件执行 BR-ASYNC-01~04
2. **File-focused review**：对指定的 async 相关文件执行 BR-ASYNC-01~04
3. **Code snippet review**：对用户提供的 async 代码片段执行 BR-ASYNC-01~04

## 输出格式

审查发现必须按以下格式输出（扩展现有 Template A）：

```markdown
### N. <问题描述>

**文件**：<path> 行 <line>
**规则**：BR-ASYNC-0x
**严重级别**：🔴 critical / 🟡 warning
**代码**：
\`\`\`
<相关代码>
\`\`\`
**问题**：<详细说明，包括为什么违规、可能导致的后果>
**修复建议**：
\`\`\`python
<修复后的代码示例>
\`\`\`
**规范依据**：CODING-021~025（参见 wiki-code-dev/references/async-reliability-rule.md）
```
