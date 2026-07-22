# Rule Catalog - Async Reliability

## Scope
- Covers: 前端异步请求（fetch/axios/SSE）的超时保护、SSE 心跳与重连、定时器生命周期清理、请求失败降级 UI 反馈。
- Does NOT cover: 后端超时与重试（属后端审查）、WebSocket 协议重连（属 WebSocket 专属规则）、服务端渲染异步边界（属 SSR 范畴）。

> 所有可配置参数（默认超时、心跳间隔、重连策略、降级 UI 模式等）集中定义在 [config/review-config.md](../config/review-config.md) 的"Async 可靠性审查参数"段。本文件只描述通用模式，不硬编码具体值。

## Rules

### AR-1: 前端 async 调用必须设置超时

IsUrgent: True
Category: Async Reliability

### Description

前端代码中所有 `await fetch()`、`await axios()`、SSE 消费等网络请求必须设置超时。超时值从 `async_reliability.default_call_timeout_sec` 读取。

未设超时的网络请求在网络卡死时会永久挂起，用户无感知且 UI 卡在 loading 状态，无法自动恢复。

排除白名单：`Promise.resolve`、`EventSource.open` 等非网络调用无需超时保护（见 `async_reliability.timeout_whitelist`）。

### Suggested Fix

使用 AbortController（fetch）或 axios timeout 配置：

```typescript
const controller = new AbortController();
const timeoutId = setTimeout(
  () => controller.abort(),
  config.async_reliability.default_call_timeout_sec * 1000
);

try {
  const response = await fetch('/api/data', { signal: controller.signal });
  const data = await response.json();
} catch (err) {
  if (err.name === 'AbortError') {
    // 降级处理
  }
} finally {
  clearTimeout(timeoutId);
}
```

### AR-2: SSE 消费必须有超时和重连机制

IsUrgent: True
Category: Async Reliability

### Description

使用 `consumeSSEStream` 或 `EventSource` 消费 SSE 流时，必须有：
1. 单次消息超时（`async_reliability.default_call_timeout_sec`）
2. 心跳检测（`async_reliability.heartbeat_interval_sec`）
3. 断线重连逻辑（`async_reliability.reconnect_max_retries`）

无超时和重连的 SSE 连接在网络波动时会静默断开，用户看到的 UI 永远停在最后一个状态，无错误提示也无自动恢复。

### Suggested Fix

```typescript
const heartbeatInterval = config.async_reliability.heartbeat_interval_sec * 1000;
let lastMessageTime = Date.now();

const eventSource = new EventSource('/api/stream');
eventSource.onmessage = (event) => {
  lastMessageTime = Date.now();
  // 处理消息
};

// 心跳检测：连续 N 次无消息判定断线
const heartbeatTimer = setInterval(() => {
  if (Date.now() - lastMessageTime > heartbeatInterval * config.async_reliability.heartbeat_miss_threshold) {
    eventSource.close();
    // 重连逻辑
  }
}, heartbeatInterval);

onBeforeUnmount(() => {
  clearInterval(heartbeatTimer);
  eventSource.close();
});
```

### AR-3: 前端看门狗定时器必须可清理

IsUrgent: True
Category: Async Reliability

### Description

前端使用 `setInterval` / `setTimeout` 实现的看门狗、心跳、轮询逻辑必须在 `onBeforeUnmount` 中清理，避免组件卸载后定时器仍在运行。

未清理的定时器会导致组件卸载后仍执行回调，访问已销毁的响应式数据，引发内存泄漏和运行时错误。虽然浏览器 JS 是单线程但非阻塞，不会像 Node.js 那样阻塞事件循环，但未清理定时器的副作用同样严重。

### Suggested Fix

```typescript
let statusTimer: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
  statusTimer = setInterval(() => {
    checkStatus();
  }, 3000);
});

onBeforeUnmount(() => {
  if (statusTimer) {
    clearInterval(statusTimer);
    statusTimer = null;
  }
});
```

### AR-4: async 请求失败必须有降级 UI 反馈

IsUrgent: True
Category: Async Reliability

### Description

前端 async 请求（fetch、SSE、axios）失败后必须有降级 UI 反馈，禁止静默失败。降级方式包括：
1. 显示错误提示（ElMessage）
2. 显示降级内容（空状态、缓存数据）
3. 提供重试按钮

仅 `console.error` 而无 UI 反馈的 catch 块属于静默失败——用户无法感知请求已失败，界面停留在上一次状态，可能基于过时数据做出错误操作。

### Suggested Fix

```typescript
try {
  const data = await fetch('/api/data').then(r => r.json());
  list.value = data;
} catch (err) {
  ElMessage.error('数据加载失败，请稍后重试');
  list.value = [];  // 降级为空列表
  hasError.value = true;  // 显示重试按钮
}
```

## Checklist
- [ ] 所有 async 网络请求设置了超时（AbortController / axios timeout）
- [ ] SSE 消费有单次消息超时、心跳检测和断线重连
- [ ] 看门狗/心跳/轮询定时器在 onBeforeUnmount 中清理
- [ ] async 请求失败有降级 UI 反馈（ElMessage / 空状态 / 重试按钮），禁止静默失败
