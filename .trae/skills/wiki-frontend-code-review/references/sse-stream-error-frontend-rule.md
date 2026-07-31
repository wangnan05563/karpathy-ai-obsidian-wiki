# SSE 流消费错误处理（FR-050）

> 复盘来源：v3 媒体生成工具的 SSE 流消费函数（consumeSSEStream）初期未吞掉 AbortError，导致用户主动停止查询时 errorMessage 被污染为"用户中止"文案；后修复为按 `err.name === 'AbortError'` 吞掉，让调用方在 finally 处理停止态。同时 finally 中 `reader.cancel()` 兜底释放时可能抛"already released"异常，需二次吞掉。
> 所有可变参数从 config/review-config.md 的 `sse_stream_error_frontend` 字段读取，禁止在规则文件中硬编码错误名或异常文案。

## 规则

### FR-050-1：SSE 流消费函数必须吞掉 AbortError，禁止污染 errorMessage 状态

- **Severity**: critical
- **Description**：SSE 流消费函数（`consumeSSEStream` / `EventSource` 消费封装）捕获异常时，必须按 `sse_stream_error_frontend.abort_error_indicators`（默认 `AbortError`）判定是否为用户主动取消，若是则直接 `return`，不抛错、不写 errorMessage。原因：用户主动停止是预期行为，不是错误；若污染 errorMessage，UI 会显示错误提示误导用户。
- **判定标准**：检索 SSE 流消费函数的 catch 块，若无 `err.name === 'AbortError'` / `err instanceof AbortError` 分支直接 return，即视为违规。修复方式：在 catch 块首行加 `if ((err as Error).name === 'AbortError') return`。

### FR-050-2：调用方必须区分"用户主动停止"与"真实错误"，用 abortReason 三态管理

- **Severity**: critical
- **Description**：调用 SSE 流消费的函数（如 `queryLLM`）必须用 `sse_stream_error_frontend.abort_reason_values`（默认 `'user' | 'timeout' | null`）三态管理停止原因：①`null` 表示正常进行中 ②`'user'` 表示用户主动停止 ③`'timeout'` 表示超时停止。禁止用 errorMessage 字段兼任停止原因标记——errorMessage 仅用于真实错误展示。
- **判定标准**：检索调用方的停止逻辑，若用 errorMessage = '用户已停止' 等文案标记用户停止，或无 abortReason 字段区分停止原因，即视为违规。修复方式：新增 abortReason ref，用户停止设 'user'，超时设 'timeout'，finally 中根据 abortReason 决定 UI 态。

### FR-050-3：finally 块必须再次 reader.cancel() 兜底释放，吞掉已释放异常

- **Severity**: critical
- **Description**：SSE 流消费函数的 finally 块必须再次调用 `reader.cancel()` 兜底释放流资源（即使 try 块正常完成，reader 可能未完全释放）。`reader.cancel()` 本身可能抛"already released" / "AbortError"异常（因流已释放），必须用 `.catch(() => {})` 或 try/catch 吞掉，避免 finally 抛错掩盖原异常。
- **判定标准**：检索 SSE 流消费函数的 finally 块，若无 `reader.cancel()` 调用，或调用未吞掉异常（无 `.catch(() => {})` 包裹），即视为违规。修复方式：`finally { reader.cancel().catch(() => {}) }`。

### FR-050-4：流消费函数的 signal 参数必须可空，未传 signal 时不影响正常消费

- **Severity**: warning
- **Description**：SSE 流消费函数的 `signal?: AbortSignal` 参数必须可选（`?` 标记），函数内部必须处理 `signal === undefined` 情况——未传 signal 时按无取消能力消费，不抛错。原因：流消费函数可能被无取消需求的调用方使用（如一次性查询），强制传 signal 会增加调用方负担。
- **判定标准**：检索 SSE 流消费函数签名，若 `signal: AbortSignal`（无 `?`），或函数内部 `signal.addEventListener('abort', ...)` 未判定 signal 是否存在，即视为违规。修复方式：`signal?: AbortSignal` + `signal?.addEventListener('abort', ...)`。

### FR-050-5：流消费中断后必须清理中途状态，禁止残留半成品数据

- **Severity**: warning
- **Description**：SSE 流消费中断（用户停止 / 超时 / 错误）后，必须清理中途状态：①流式拼接的半成品 answer 文本须标记为"已中断"或截断 ②isLoading / isStreaming 标志必须复位为 false ③refs / images 等部分数据须决定保留或清空（按 `sse_stream_error_frontend.partial_data_strategy`）。禁止留 isLoading=true 导致 UI 卡 loading 态。
- **判定标准**：检索 SSE 流消费的中断处理逻辑，若 isLoading / isStreaming 未在中断时复位，或半成品数据未按策略处理，即视为违规。修复方式：在 finally 块中复位 isLoading=false，按 partial_data_strategy 处理半成品数据。

## 适用场景

- Vue 3 / React 项目中消费 SSE 流式接口（`fetch` + `ReadableStream` / `EventSource`）。
- 支持用户主动停止流式查询的场景（"停止生成"按钮）。
- 流式查询有超时限制的场景（LLM 长查询、媒体生成进度）。

## 不适用场景

- 不支持取消的一次性请求（无 signal 参数，无停止按钮）。
- WebSocket 全双工通信（关闭机制不同，用 `ws.close()`）。
- 静态资源加载（无流式消费语义）。
- 单元测试中的 mock 流（测试本身验证错误处理逻辑）。

## 检查流程

```
[开始] 扫描 .vue / .ts 文件中的 SSE 流消费函数
  │
  ▼
[1] AbortError 吞掉检查（FR-050-1）
  │  └─ 检索 consumeSSEStream / fetch stream 的 catch 块
  │       └─ 无 err.name === 'AbortError' 分支 → 标记违规
  │       └─ 有 AbortError 分支但未 return（仍写 errorMessage）→ 标记违规
  │
  ▼
[2] abortReason 三态检查（FR-050-2）
  │  └─ 检索调用 SSE 消费的函数
  │       └─ 用 errorMessage 标记用户停止 → 标记违规
  │       └─ 无 abortReason 字段区分停止原因 → 标记违规
  │
  ▼
[3] finally reader.cancel() 检查（FR-050-3）
  │  └─ 检索 SSE 消费函数的 finally 块
  │       └─ 无 reader.cancel() → 标记违规
  │       └─ reader.cancel() 未 .catch(() => {}) → 标记违规
  │
  ▼
[4] signal 参数可空检查（FR-050-4）
  │  └─ 检索 SSE 消费函数签名
  │       └─ signal: AbortSignal（无 ?）→ 标记违规
  │       └─ signal.addEventListener 未判空 → 标记违规
  │
  ▼
[5] 中途状态清理检查（FR-050-5）
  │  └─ 检索中断处理逻辑（finally / catch）
  │       └─ isLoading / isStreaming 未复位 → 标记违规
  │       └─ 半成品数据未按 partial_data_strategy 处理 → 标记违规
  │
  ▼
[结束] 输出审查报告
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `sse_stream_error_frontend.enabled` | `true` | 是否启用 SSE 流消费错误处理审查 |
| `sse_stream_error_frontend.abort_error_indicators` | `AbortError` | 标识用户主动取消的错误名（逗号分隔，匹配 err.name） |
| `sse_stream_error_frontend.abort_reason_values` | `user, timeout, null` | abortReason 三态枚举值（逗号分隔） |
| `sse_stream_error_frontend.reader_release_error_indicators` | `already released, AbortError, InvalidStateError` | reader.cancel() 可能抛的异常指示（逗号分隔，须吞掉） |
| `sse_stream_error_frontend.signal_param_optional` | `true` | signal 参数是否必须可选（`?` 标记） |
| `sse_stream_error_frontend.partial_data_strategy` | `mark_truncated` | 中断后半成品数据处理策略（`mark_truncated`=标记截断 / `discard`=丢弃 / `keep`=保留） |
| `sse_stream_error_frontend.loading_state_fields` | `isLoading, isStreaming, isGenerating` | 中断时必须复位的 loading 状态字段名（逗号分隔） |
| `sse_stream_error_frontend.finally_cleanup_required` | `true` | 是否强制 finally 块清理 reader |

## 检查方式

1. **SSE 消费函数扫描**：在 `.vue` / `.ts` 文件中检索 `consumeSSEStream` / `getReader()` / `EventSource` / `ReadableStream`，定位流消费代码。
2. **catch 块分析**：对每个流消费的 catch 块，检索 `abort_error_indicators` 中的错误名，验证是否有对应 return 分支。
3. **abortReason 字段检查**：检索调用 SSE 消费的函数，验证是否有 `abortReason` ref 且取值 ∈ `abort_reason_values`。
4. **finally 块检查**：检索流消费函数的 finally 块，验证是否有 `reader.cancel()` 且用 `.catch(() => {})` 吞掉异常。
5. **signal 参数检查**：检索流消费函数签名，验证 `signal` 是否为可选参数（`?`），函数内部是否用 `signal?.` 可选链调用。
6. **loading 状态复位检查**：检索中断处理（finally / catch），验证 `loading_state_fields` 中的字段是否复位为 false。

## 正确示例

```ts
// ✅ SSE 流消费函数（FR-050-1/3/4）
async function consumeSSEStream(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  onEvent: (event: SSEEvent) => void,
  signal?: AbortSignal  // ✅ signal 可空（FR-050-4）
) {
  const decoder = new TextDecoder()
  let buffer = ''

  // ✅ signal 可空时安全监听（FR-050-4）
  signal?.addEventListener('abort', () => {
    reader.cancel().catch(() => {})  // ✅ 吞掉已释放异常
  })

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          onEvent({ type: line.slice(7), data: buffer })
        }
      }
    }
  } catch (err) {
    // ✅ 吞掉 AbortError（FR-050-1）
    if ((err as Error).name === 'AbortError') return
    throw err  // 真实错误向上抛
  } finally {
    // ✅ finally 块 reader.cancel() 兜底释放，吞掉异常（FR-050-3）
    reader.cancel().catch(() => {})
  }
}
```

```ts
// ✅ 调用方：abortReason 三态管理（FR-050-2/5）
import { ref, onBeforeUnmount } from 'vue'

const answer = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
// ✅ abortReason 三态：null（进行中）/ 'user' / 'timeout'（FR-050-2）
const abortReason = ref<'user' | 'timeout' | null>(null)
let abortController: AbortController | null = null

async function queryLLM(prompt: string) {
  isLoading.value = true
  errorMessage.value = ''
  answer.value = ''
  abortReason.value = null  // ✅ 重置为进行中
  abortController = new AbortController()

  try {
    const res = await fetch('/api/query', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
      signal: abortController.signal
    })
    const reader = res.body!.getReader()
    await consumeSSEStream(reader, handleEvent, abortController.signal)
  } catch (err) {
    // ✅ AbortError 已被 consumeSSEStream 吞掉，这里只处理真实错误
    errorMessage.value = (err as Error).message
  } finally {
    // ✅ 复位 loading 状态（FR-050-5）
    isLoading.value = false
    abortController = null
  }
}

// ✅ 用户主动停止：设 abortReason = 'user'（FR-050-2）
function stopQuery() {
  abortReason.value = 'user'
  abortController?.abort()
}

// ✅ 超时停止：设 abortReason = 'timeout'（FR-050-2）
function onTimeout() {
  abortReason.value = 'timeout'
  abortController?.abort()
}

// ✅ 中断后处理半成品数据（FR-050-5）
watch(abortReason, (reason) => {
  if (reason !== null && answer.value) {
    // 按 partial_data_strategy = mark_truncated 标记截断
    answer.value += '\n\n[已中断]'
  }
})

onBeforeUnmount(() => {
  abortController?.abort()
})
```

## 错误示例

```ts
// ❌ 未吞掉 AbortError，污染 errorMessage（FR-050-1 违规）
async function consumeSSEStream(reader: ReadableStreamDefaultReader, onEvent: Function, signal?: AbortSignal) {
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      onEvent(value)
    }
  } catch (err) {
    // ❌ 未判定 AbortError，用户主动停止也走 errorMessage
    errorMessage.value = (err as Error).message  // ❌ "用户已中止" 污染 errorMessage
  }
}

// ❌ 用 errorMessage 标记用户停止（FR-050-2 违规）
function stopQuery() {
  abortController?.abort()
  // ❌ 用 errorMessage 文案标记停止原因，无法区分"用户停止"与"真实错误"
  errorMessage.value = '用户已停止查询'
}

// ❌ finally 块未 reader.cancel() 兜底（FR-050-3 违规）
async function consumeSSEStream(reader: ReadableStreamDefaultReader, onEvent: Function) {
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      onEvent(value)
    }
  } catch (err) {
    if ((err as Error).name === 'AbortError') return
    throw err
  }
  // ❌ 无 finally 块，reader 可能未完全释放 → 流资源泄漏
}

// ❌ reader.cancel() 未吞掉异常（FR-050-3 违规）
async function consumeSSEStream(reader: ReadableStreamDefaultReader, onEvent: Function) {
  try {
    // ...
  } finally {
    reader.cancel()  // ❌ 未 .catch(() => {})，可能抛 "already released" 异常掩盖原错误
  }
}

// ❌ signal 参数未设为可选（FR-050-4 违规）
async function consumeSSEStream(
  reader: ReadableStreamDefaultReader,
  onEvent: Function,
  signal: AbortSignal  // ❌ 无 ?，调用方必须传 signal
) {
  signal.addEventListener('abort', () => {  // ❌ 未判空，signal 为 undefined 时报错
    reader.cancel()
  })
}

// ❌ 中断后 isLoading 未复位（FR-050-5 违规）
async function queryLLM(prompt: string) {
  isLoading.value = true
  try {
    await consumeSSEStream(reader, handleEvent)
  } catch (err) {
    errorMessage.value = (err as Error).message
  }
  // ❌ 无 finally 块，异常时 isLoading 留 true → UI 卡 loading 态
}
```

## 与其他规则的关系

- **FR-048（长短任务架构分离）**：FR-048-1 决定任务走 SSE 流，FR-050 约束 SSE 流的错误处理。两者互补：FR-048 是架构选择，FR-050 是错误处理实现。
- **FR-049（SSE 事件对象映射分发）**：FR-049 约束事件分发结构，FR-050 约束流消费的错误处理。两者共同覆盖 SSE 流消费的前端实现。
- **FR-051（长任务轮询 UI 模式）**：FR-050-2 的 abortReason 三态与 FR-051-4 的 abortReason 三态一致，SSE 流与轮询任务共用停止原因管理逻辑。
- **AR-1~AR-4（Async 可靠性）**：AR-3 约束定时器清理，FR-050-3 约束 reader 清理，两者分属不同资源类型但都要求 finally 兜底。

## 适配新项目

- **React / Next.js**：`ref` 改为 `useState` / `useRef`；`watch` 改为 `useEffect`；`onBeforeUnmount` 改为 `useEffect` cleanup；AbortError 吞掉逻辑不变。
- **Vue 2**：`ref` 改为 `data()`；`watch` 语法不变；`onBeforeUnmount` 改为 `beforeDestroy`；其余规则不变。
- **纯 JavaScript**：去掉 TypeScript 类型注解，AbortError 吞掉与 finally 清理逻辑不变。
- **EventSource 项目**：`reader.cancel()` 改为 `eventSource.close()`；AbortError 改为 `eventSource.readyState === EventSource.CLOSED` 判定；其余规则不变。
- **fetch + ReadableStream 项目（非 SSE）**：流消费错误处理逻辑通用，`consumeSSEStream` 改为通用 `consumeStream`，AbortError 吞掉与 finally 清理规则不变。
