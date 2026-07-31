# SSE 流消费错误处理规则（CODING-064）

> 复盘来源：v3 媒体生成工具开发中，前端 SSE 流消费函数遇到两类问题：①用户主动停止生成时，AbortController 触发 AbortError，但错误处理逻辑把 AbortError 当作真实错误显示给用户，污染 errorMessage 状态；②流消费函数结束后未调用 `reader.cancel()` 兜底释放，导致浏览器连接资源泄漏。统一为：AbortError 静默吞掉、finally 中再次 cancel、signal 参数可空。
> 本规则为行为规则，无可变参数，所有逻辑为运行时约定。

## 规则

**前端 SSE 流消费函数必须遵守四项契约**：

1. **吞掉 AbortError**：SSE 流消费函数必须吞掉 AbortError（`err.name === 'AbortError'` 直接 return），让调用方在 finally 处理停止态
2. **区分主动停止与真实错误**：调用方需区分"用户主动停止"和"真实错误"，避免主动取消污染 errorMessage 状态
3. **finally 中再次 cancel 兜底**：finally 中必须再次 `reader.cancel()` 兜底释放，吞掉已释放异常（`reader` 可能已 closed）
4. **signal 参数可空**：流消费函数的 signal 参数必须可空，未传 signal 时不影响正常消费

## 适用场景

- 前端 SSE 流式响应消费（LLM 流式输出、媒体生成进度）
- 用 AbortController 主动停止流消费的场景
- 用 ReadableStream reader 的流消费（fetch + body.getReader()）
- 需要清理浏览器连接资源的流消费

## 不适用场景

- 后端 SSE 流写入（用 `reply.raw.write` + `reply.raw.end()`，无需 AbortError 处理）
- WebSocket 消费（用 WebSocket API 的 close 事件，无需 AbortController）
- 一次性 JSON 请求（无流消费，无需 cancel）
- 同步迭代器消费（用 for...of + break，无需 AbortError）

## 关键参数

本规则为行为规则，无可变参数。所有逻辑为运行时约定：
- `AbortError` 判定：`err.name === 'AbortError'`
- 已释放异常判定：`reader.closed === true` 或 catch 中静默
- signal 可空：`signal?: AbortSignal`

## 检查方式

1. **AbortError 吞掉检查**：catch 块必须先判断 `err.name === 'AbortError'`，命中则直接 return，不更新 errorMessage
2. **主动停止与真实错误区分检查**：调用方需用 `abortReason: 'user' | 'timeout' | null` 区分停止原因，主动停止不显示错误
3. **finally cancel 检查**：finally 块必须调用 `reader.cancel()`，且用 try/catch 吞掉已释放异常
4. **signal 可空检查**：流消费函数签名必须为 `signal?: AbortSignal`，函数内用 `signal?.addEventListener` 或 `if (signal) signal.addEventListener`

## 正确示例

```typescript
// frontend/src/stores/query.ts
import { ref } from 'vue';

const isGenerating = ref(false);
const errorMessage = ref('');
const abortReason = ref<'user' | 'timeout' | null>(null);
let abortController: AbortController | null = null;

/**
 * 消费 SSE 流——吞掉 AbortError + finally 兜底 cancel
 * 为什么吞掉 AbortError：AbortController 触发的 AbortError 是用户主动停止，
 * 不是真实错误，显示给用户会造成困惑（"我点停止，却弹错误提示"）。
 */
async function consumeSSEStream(
  response: Response,
  onEvent: (event: string, data: any) => void,
  signal?: AbortSignal, // ✅ signal 参数可空
): Promise<void> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      // 解析 SSE 事件...
      const events = parseSSEEvents(buffer);
      buffer = events.remainder;
      for (const evt of events.parsed) {
        onEvent(evt.name, evt.data);
      }
    }
  } catch (err) {
    // ✅ 吞掉 AbortError（用户主动停止）
    if (err instanceof Error && err.name === 'AbortError') {
      return; // 不更新 errorMessage，让调用方在 finally 处理停止态
    }
    // 真实错误才更新 errorMessage
    throw err;
  } finally {
    // ✅ finally 中再次 cancel 兜底释放，吞掉已释放异常
    try {
      await reader.cancel();
    } catch {
      // reader 可能已 closed，静默吞掉
    }
  }
}

/**
 * 调用方：区分主动停止与真实错误
 */
async function generate() {
  isGenerating.value = true;
  errorMessage.value = '';
  abortReason.value = null;
  abortController = new AbortController();

  try {
    const response = await fetch('/api/query', {
      method: 'POST',
      signal: abortController.signal,
      body: JSON.stringify({ prompt: '...' }),
    });
    await consumeSSEStream(response, handleEvent, abortController.signal);
  } catch (err) {
    // ✅ 区分主动停止与真实错误
    if (abortReason.value === 'user' || abortReason.value === 'timeout') {
      // 主动停止，不显示错误
      return;
    }
    errorMessage.value = err instanceof Error ? err.message : String(err);
  } finally {
    isGenerating.value = false;
  }
}

/**
 * 用户主动停止
 */
function stopGeneration() {
  abortReason.value = 'user'; // ✅ 标记停止原因
  abortController?.abort();
}

/**
 * 超时停止
 */
function onTimeout() {
  abortReason.value = 'timeout'; // ✅ 标记停止原因
  abortController?.abort();
}
```

## 错误示例

```typescript
// ❌ 错误：AbortError 当作真实错误显示给用户
async function consumeSSE(response: Response) {
  const reader = response.body!.getReader();
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      // ...
    }
  } catch (err) {
    // ⚠️ 未判断 AbortError，用户主动停止也显示错误
    errorMessage.value = err.message;
  }
}

// ❌ 错误：未在 finally 中 cancel 兜底释放
async function consumeSSE(response: Response) {
  const reader = response.body!.getReader();
  try {
    // ...
  } catch (err) {
    if (err.name === 'AbortError') return;
    throw err;
  }
  // ⚠️ 缺少 finally { reader.cancel() }，浏览器连接资源泄漏
}

// ❌ 错误：signal 参数必填，无法在不传 signal 时消费
async function consumeSSE(response: Response, signal: AbortSignal) { // ⚠️ signal 必填
  // ...
}
// 调用方：consumeSSE(response) // ❌ 编译报错，必须传 signal

// ❌ 错误：finally 中 cancel 不吞异常，已 closed 时抛错
finally {
  await reader.cancel(); // ⚠️ reader 可能已 closed，抛 TypeError
}

// ❌ 错误：未区分主动停止与真实错误，停止后显示错误
function stopGeneration() {
  abortController?.abort();
  // ⚠️ 未设置 abortReason，调用方 catch 会把 AbortError 当真实错误
}
```

## 适配新项目

- 适配 React：用 `useRef<AbortController>` 替代模块级变量，useEffect cleanup 中 abort
- 适配原生 EventSource：EventSource 自带 close 方法，无需 AbortController，但需在 close 后移除事件监听
- 适配 WebSocket：用 `websocket.close()` 替代 `abortController.abort()`，close 事件处理停止态
- 适配 React Query / SWR：用库自带的 cancel 机制，无需手写 AbortController
- 适配 service worker：流消费在 service worker 中，需 postMessage 通知主线程停止态

## 与其他规则的关系

- 与 CODING-063（SSE 事件对象映射分发）联动：本规则的 onEvent 回调调用对象映射表中的 handler
- 与 CODING-065（长任务轮询 UI 模式）联动：长任务不走 SSE，走轮询，停止机制用 `clearInterval` 替代 `abortController.abort()`
- 与 CODING-066（事件委托 + 生命周期清理）联动：组件卸载时必须 abort 进行中的 SSE 流，避免内存泄漏
- 与 CODING-057（超时分级策略）联动：SSE 流的超时用 `setTimeout` + `abortController.abort()`，而非 `AbortSignal.timeout`（因需同步设 abortReason）
