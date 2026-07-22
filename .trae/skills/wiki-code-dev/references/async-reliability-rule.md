# Async 可靠性守卫规则

> 本规则抽象自浏览器登录 91s 超时问题的两次修复复盘。
> 所有可变参数从 `config/tech-stack.json` 的 `async_reliability` 字段读取，禁止在业务代码或规则文件硬编码。
> 适用项目：xianyu-hunter（Python/asyncio/Playwright）、Karpathy Wiki（TypeScript/AsyncIterable/SSE）及其他使用 async/await + IPC 的项目。

## CODING-021：async 调用必须设置超时（强制）

**严重级别**：critical

**规则**：禁止直接 `await` 任何可能阻塞的 async 调用（IPC、网络、文件 I/O、外部进程通信）。必须用 `asyncio.wait_for(coro, timeout=config.async_reliability.default_call_timeout_sec)`（Python）或 `Promise.race([promise, timeout])`（TypeScript）包裹。

**根因**：Playwright `context.cookies()`、Node.js `fetch()`、`fs.promises.readFile()` 等 async API 在底层 IPC 通道异常或外部进程卡死时会**永久挂起**，既不抛错也不返回。`await` 后的代码无法执行，导致心跳更新停滞、子进程被误判"无响应"。

**正确模板**（Python asyncio）：
```python
import asyncio

try:
    cookies = await asyncio.wait_for(
        context.cookies(),
        timeout=config.async_reliability.default_call_timeout_sec,  # 5.0
    )
except asyncio.TimeoutError:
    cookies = best  # 降级到上次已知值
```

**正确模板**（TypeScript）：
```typescript
const cookies = await Promise.race([
  context.cookies(),
  timeout(config.async_reliability.default_call_timeout_sec * 1000),
]);
```

**错误示例**：
```python
# 违规：无超时保护，context.cookies() 可能永久挂起
cookies = await context.cookies()
```

**检查方式**：Grep `await\s+\w+\.` 在 async 函数中的调用，确认是否被 `wait_for` / `Promise.race` 包裹。白名单见 `config.async_reliability.timeout_whitelist`。

## CODING-022：事件循环阻塞场景必须使用线程级保护（强制）

**严重级别**：critical

**规则**：当 async 调用可能阻塞整个事件循环（如 Playwright IPC、Node.js native addon）时，心跳/看门狗逻辑必须用 `threading.Thread`（Python）或 `worker_threads`（Node.js）实现，禁止用 `asyncio.Task` / `Promise.then`。

**根因**：`asyncio.Task` 和 `Promise.then` 都依赖事件循环调度。当事件循环线程被阻塞时，**所有 asyncio Task 都无法执行**，包括所谓"独立"的心跳 Task。只有操作系统调度的线程才能在事件循环阻塞时继续运行。

**正确模板**（Python threading）：
```python
import threading

_heartbeat_stop = threading.Event()

def _heartbeat_thread():
    while not _heartbeat_stop.is_set():
        time.sleep(config.async_reliability.heartbeat_interval_sec)  # 3.0
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

**错误示例**：
```python
# 违规：asyncio.Task 在事件循环阻塞时无法调度
async def _heartbeat():
    while True:
        await asyncio.sleep(3)
        _emit_status("running", "进行中...")

heartbeat_task = asyncio.create_task(_heartbeat())  # 事件循环阻塞后失效
```

**检查方式**：审查心跳/看门狗/状态更新逻辑，若涉及可能阻塞事件循环的 async 调用（见 `config.async_reliability.blocking_risk_apis`），必须确认心跳使用线程实现。

## CODING-023：状态文件通信必须独立于业务事件循环（强制）

**严重级别**：critical

**规则**：子进程通过状态文件（JSON/YAML）与主进程通信时，状态文件的 `ts`（时间戳）字段更新逻辑必须满足以下任一条件：
1. 由独立线程写入（推荐）
2. 由业务循环内的同步代码写入，且循环间隔 ≤ `config.async_reliability.heartbeat_max_interval_sec`

**根因**：主进程通过 `ts` 字段判断子进程是否存活（如 90s 未更新则判定"无响应"）。若 `ts` 更新依赖业务 async 循环，当循环被 IPC 阻塞时 `ts` 停止更新，主进程误判子进程死亡，强制终止正常但缓慢的子进程。

**正确模板**：
```python
# 独立线程写 ts，与业务循环解耦
def _heartbeat_thread():
    while not _heartbeat_stop.is_set():
        time.sleep(config.async_reliability.heartbeat_interval_sec)
        _write_status_file({"ts": time.time(), "status": "running"})

# 业务循环即使卡住，心跳线程仍更新 ts
```

**检查方式**：
1. Grep 状态文件写入函数（如 `_write_status`、`_emit_status`、`set_status`）
2. 确认调用方是否在独立线程中，或在业务循环的同步代码路径上
3. 若在 async 循环中，确认循环间隔 ≤ `heartbeat_max_interval_sec`

## CODING-024：async 调用超时必须提供兜底数据（强制）

**严重级别**：warning

**规则**：`asyncio.wait_for` / `Promise.race` 超时后，必须有兜底数据返回，禁止直接抛错终止流程。兜底数据通过 `best_holder` 模式（可变容器）或闭包变量传递。

**根因**：`asyncio.wait_for` 超时会取消被等待的协程，但取消信号在 IPC future 上可能无法传播（Playwright 1.60.0 的 `_channel.send` 在浏览器进程无响应时 cancel 不完整）。此时协程的返回值丢失，若没有兜底数据，后续流程无法继续。

**正确模板**：
```python
best_holder: list[dict] = []  # 可变容器，供协程内部写入

async def _collect_with_fallback():
    best = []
    while True:
        try:
            current = await asyncio.wait_for(context.cookies(), timeout=5.0)
        except asyncio.TimeoutError:
            current = best
        if len(current) >= len(best):
            best = current
            best_holder.clear()      # 同步到外部容器
            best_holder.extend(best)
        # ... 循环退出条件

try:
    result = await asyncio.wait_for(_collect_with_fallback(), timeout=30.0)
except asyncio.TimeoutError:
    result = best_holder  # 兜底：最后已知数据
```

**错误示例**：
```python
# 违规：超时后无兜底，result 未定义
try:
    result = await asyncio.wait_for(blocking_call(), timeout=30.0)
except asyncio.TimeoutError:
    raise RuntimeError("超时")  # 流程终止，无法降级
```

**检查方式**：审查 `asyncio.wait_for` 的 except 分支，确认是否有兜底数据赋值，而非直接 raise 或 pass。

## CODING-025：长时 async 任务必须多层超时防护（建议）

**严重级别**：suggestion

**规则**：长时 async 任务（登录、爬取、批量处理）必须设置多层超时：
1. **单次调用超时**：`config.async_reliability.default_call_timeout_sec`（5s）
2. **阶段硬超时**：`config.async_reliability.stage_hard_timeout_sec`（30s）
3. **整体任务超时**：`config.async_reliability.task_total_timeout_sec`（180s）

**根因**：单一超时无法应对不同层级的阻塞。单次调用可能卡 5s 后恢复，但整个阶段可能需要 30s 才能完成；若只设整体超时，单次卡住会消耗整体预算。

**正确模板**：
```python
# 三层超时
try:
    # 第 1 层：单次调用（在 _collect_settled_cookies 内部）
    cookies = await asyncio.wait_for(context.cookies(), timeout=5.0)
    
    # 第 2 层：阶段硬超时（在外层包裹）
    final = await asyncio.wait_for(_collect_settled_cookies(), timeout=30.0)
finally:
    # 第 3 层：整体任务超时（由主进程 kill 子进程实现）
    pass
```

**检查方式**：审查长时 async 任务的超时配置，确认至少有 2 层超时保护。

## 多层防护决策表

| 阻塞级别 | 现象 | 适用规则 | 解决方案 |
|---------|------|---------|---------|
| Level 1 | 单次 async 调用卡住 | CODING-021 | `asyncio.wait_for` 单次超时 |
| Level 2 | 整个阶段卡住 | CODING-024 + CODING-025 | 外层硬超时 + 兜底数据 |
| Level 3 | 事件循环被阻塞 | CODING-022 + CODING-023 | 线程级心跳 + 独立状态更新 |
| Level 4 | 子进程完全无响应 | 主进程 kill | 超出本规则范围，由主进程心跳检测处理 |

## 适用场景与不适用场景

### 适用场景
- Python asyncio + Playwright/aiohttp/异步 IPC 的项目
- Node.js + Playwright/native addon 的项目
- 子进程通过状态文件与主进程通信的架构
- 需要心跳检测的长时任务（登录、爬取、批量处理）
- 使用 SSE 流式响应且需要保活检测的场景

### 不适用场景
- 纯同步代码（无需 asyncio，用 threading.Timer 即可）
- 单次快速 async 调用（<1s，阻塞风险可忽略）
- 无子进程通信的简单 Web API
- CI/CD 流水线任务（通常有独立的超时机制）

## 故障排查 Checklist

当出现"进程无响应"或"超时未更新"错误时，按顺序排查：

1. **状态文件分析**：读取状态文件，对比 `timings` 字段，定位卡死的阶段
2. **超时配置检查**：确认卡死阶段的 async 调用是否有 `asyncio.wait_for` 包裹
3. **心跳实现检查**：确认心跳是 `asyncio.Task`（违规）还是 `threading.Thread`（合规）
4. **事件循环阻塞验证**：若 `asyncio.Task` 心跳也失效，说明事件循环被阻塞，需升级为线程
5. **兜底数据验证**：确认超时后是否有 `best_holder` 兜底，而非直接抛错
6. **多层超时审查**：确认是否有单次/阶段/整体三层超时配置
