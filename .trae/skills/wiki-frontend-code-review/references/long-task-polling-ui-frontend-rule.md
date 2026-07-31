# 长任务轮询 UI 模式（FR-051）

> 复盘来源：v3 媒体生成工具的视频生成任务初期用 `AbortSignal.timeout` 设超时，但无法同步标记 abortReason 区分"超时停止"与"用户停止"；后改为 `setTimeout` + 手动 abort + 设 abortReason='timeout'。同时"关闭对话框"与"重置状态保持对话框"初期合为一个函数，导致用户想重新生成时被迫重开对话框；后拆为两个独立函数。轮询单次失败初期会终止整个轮询，网络抖动时体验差；后改为单次失败仅更新 error 文案不终止。
> 所有可变参数从 config/review-config.md 的 `long_task_polling_ui_frontend` 字段读取，禁止在规则文件中硬编码轮询间隔、状态枚举或超时阈值。

## 规则

### FR-051-1：长任务轮询必须用 setInterval + 状态机驱动 UI，禁止单一 loading 态

- **Severity**: critical
- **Description**：长任务（视频生成、批量处理等）前端轮询必须用 `setInterval(poll_interval_ms)` 定时查询状态，并用 `long_task_polling_ui_frontend.state_machine_values`（默认 `idle, queued, processing, completed, failed`）五状态机驱动 UI 模板切换。禁止用单一 `isLoading: boolean` 表达长任务全生命周期——用户无法区分"排队中"与"处理中"，无法在"完成"与"失败"时正确切换 UI。
- **判定标准**：检索长任务轮询代码，若仅有 `isLoading` / `isPending` 单一布尔态，或状态枚举不完整（缺失 `long_task_polling_ui_frontend.state_machine_values` 中的任一值），即视为违规。修复方式：改为 `taskState: ref<'idle' | 'queued' | 'processing' | 'completed' | 'failed'>('idle')`，按状态驱动 UI。

### FR-051-2：轮询单次失败不终止，仅更新 error 文案，容忍网络抖动

- **Severity**: critical
- **Description**：轮询单次请求失败（网络抖动、服务暂不可用）不得终止整个轮询循环，仅更新 error 文案提示用户当前查询失败但仍在重试。原因：长任务轮询持续数分钟，单次失败概率高，终止后用户需手动重启轮询体验差。仅当任务状态变为 `completed` / `failed` 或用户主动停止时才终止轮询。
- **判定标准**：检索轮询单次请求的 catch 块，若 `clearInterval(pollTimer)` / `stopPolling()` 在 catch 中调用，即视为违规。修复方式：catch 中仅 `errorMessage.value = '查询失败，重试中...'`，不停止轮询。

### FR-051-3：完成/失败必须显式停止定时器，禁止依赖 onBeforeUnmount 兜底

- **Severity**: critical
- **Description**：轮询检测到任务状态变为 `completed` 或 `failed` 时，必须显式调用 `stopXxxPolling()` 清理 `setInterval` 定时器，禁止仅依赖 `onBeforeUnmount` 兜底。原因：若不清定时器，组件未卸载时会持续轮询已完成的任务，浪费请求配额；onBeforeUnmount 仅在组件卸载时触发，非任务完成时。
- **判定标准**：检索轮询回调中状态判定逻辑，若 `completed` / `failed` 分支无 `clearInterval` / `stopPolling` 调用，即视为违规。修复方式：在状态判定分支中显式停止定时器。

### FR-051-4：超时必须用 setTimeout 而非 AbortSignal.timeout，以同步设 abortReason 标记

- **Severity**: critical
- **Description**：长任务超时控制必须用 `setTimeout(timeout_ms)` + 手动 `abortController.abort()` + `abortReason.value = 'timeout'`，禁止用 `AbortSignal.timeout(timeout_ms)`。原因：`AbortSignal.timeout` 触发 abort 时无法同步设置 abortReason，调用方在 catch 中无法区分"超时停止"与"用户主动停止"——两者都抛 AbortError。用 setTimeout 可在 abort 前先设 abortReason='timeout'，调用方据此区分。
- **判定标准**：检索长任务超时控制代码，若用 `AbortSignal.timeout(...)`，即视为违规。修复方式：改为 `const timer = setTimeout(() => { abortReason.value = 'timeout'; abortController.abort() }, timeout_ms)`。

### FR-051-5："关闭对话框"与"重置状态保持对话框"必须拆为两个函数

- **Severity**: warning
- **Description**：长任务对话框的操作必须区分两个场景拆为独立函数：①`closeDialog()`：停止轮询 + 关闭对话框 + 重置全部状态（用于用户完成查看后关闭）②`resetState()`：停止轮询 + 清状态，但保持对话框打开（用于用户想重新生成）。禁止合为一个函数用参数区分——调用方易传错参数，且"保持对话框"场景需额外手动开对话框。
- **判定标准**：检索长任务对话框的操作函数，若用 `handleClose(keepOpen: boolean)` 等单函数 + 参数模式，即视为违规。修复方式：拆为 `closeDialog()` 与 `resetState()` 两个独立函数。

### FR-051-6：onBeforeUnmount 必须清理 abortController + 所有 addEventListener + setInterval timer

- **Severity**: critical
- **Description**：长任务组件的 `onBeforeUnmount` 必须清理三类资源：①`abortController.abort()` 取消进行中请求 ②所有 `addEventListener` 注册的监听器（函数引用须保存以便 remove）③`setInterval` / `setTimeout` 定时器（须保存 id 以便 clear）。禁止仅清理其一，否则内存泄漏或回调飞溅。
- **判定标准**：检索长任务组件的 `onBeforeUnmount`，若未清理上述三类资源中的任一（且组件中使用了该类资源），即视为违规。修复方式：补齐清理逻辑，监听器须保存函数引用。

## 适用场景

- Vue 3 / React 项目中长任务（视频生成、批量处理、AI 训练任务等）的前端轮询 UI。
- 任务耗时 > 30 秒，需状态机驱动 UI 切换的场景。
- 支持用户主动停止 + 超时停止 + 重新生成的对话框交互。

## 不适用场景

- 短任务（≤ 30 秒）走 SSE 流（参见 FR-048）。
- 一次性请求（无轮询需求）。
- WebSocket 实时推送（无需轮询，服务端主动推送状态）。
- 后台任务（无 UI 交互，如 Service Worker 定时同步）。

## 检查流程

```
[开始] 扫描 .vue / .ts 文件中的长任务轮询代码
  │
  ▼
[1] 状态机完整性检查（FR-051-1）
  │  └─ 检索 setInterval / poll 调用
  │       └─ 状态枚举是否含 state_machine_values 全部值
  │            └─ 仅 isLoading 布尔态 → 标记违规
  │            └─ 状态枚举缺值 → 标记违规
  │
  ▼
[2] 单次失败不终止检查（FR-051-2）
  │  └─ 检索轮询单次请求的 catch 块
  │       └─ catch 中 clearInterval / stopPolling → 标记违规
  │
  ▼
[3] 完成/失败显式停止检查（FR-051-3）
  │  └─ 检索轮询回调的状态判定
  │       └─ completed/failed 分支无 clearInterval → 标记违规
  │
  ▼
[4] 超时实现方式检查（FR-051-4）
  │  └─ 检索长任务超时控制
  │       └─ AbortSignal.timeout(...) → 标记违规
  │       └─ setTimeout + abort + abortReason='timeout' → 合规
  │
  ▼
[5] 关闭/重置函数拆分检查（FR-051-5）
  │  └─ 检索长任务对话框操作函数
  │       └─ 单函数 + 参数模式 → 标记违规
  │       └─ 拆为 closeDialog() / resetState() → 合规
  │
  ▼
[6] onBeforeUnmount 清理检查（FR-051-6）
  │  └─ 检索 onBeforeUnmount 块
  │       └─ 未清理 abortController → 标记违规
  │       └─ 未清理 addEventListener（监听器引用未保存）→ 标记违规
  │       └─ 未清理 setInterval/setTimeout → 标记违规
  │
  ▼
[结束] 输出审查报告
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `long_task_polling_ui_frontend.enabled` | `true` | 是否启用手任务轮询 UI 审查 |
| `long_task_polling_ui_frontend.poll_interval_ms` | `5000` | 轮询间隔（毫秒） |
| `long_task_polling_ui_frontend.timeout_ms` | `300000` | 长任务超时（毫秒，默认 5 分钟） |
| `long_task_polling_ui_frontend.state_machine_values` | `idle, queued, processing, completed, failed` | 五状态机枚举值（逗号分隔） |
| `long_task_polling_ui_frontend.abort_reason_values` | `user, timeout, null` | abortReason 三态（与 FR-050-2 一致） |
| `long_task_polling_ui_frontend.single_failure_strategy` | `update_error_only` | 单次失败策略（`update_error_only`=仅更新文案 / `terminate`=终止，默认前者） |
| `long_task_polling_ui_frontend.close_function_name` | `closeDialog` | 关闭对话框函数名 |
| `long_task_polling_ui_frontend.reset_function_name` | `resetState` | 重置状态函数名 |
| `long_task_polling_ui_frontend.cleanup_hooks` | `onBeforeUnmount` | 资源清理生命周期钩子（逗号分隔） |
| `long_task_polling_ui_frontend.required_cleanup_targets` | `abortController, eventListeners, timers` | onBeforeUnmount 必须清理的资源类型（逗号分隔） |
| `long_task_polling_ui_frontend.long_task_names` | `video, batch, podcast` | 长任务名清单（与 FR-048 共用，触发本规则） |

## 检查方式

1. **轮询调用扫描**：在 `.vue` / `.ts` 文件中检索 `setInterval` / `poll` / `long_task_names` 中的任务名，定位轮询代码。
2. **状态机核对**：检索状态枚举声明，与 `state_machine_values` 比对完整性。
3. **catch 块分析**：检索轮询单次请求的 catch 块，验证是否有 `clearInterval` / `stopPolling`（违规）。
4. **完成/失败分支检查**：检索轮询回调的状态判定，验证 `completed` / `failed` 分支是否有显式停止定时器。
5. **超时实现检查**：检索 `AbortSignal.timeout` 调用，命中即违规；验证 `setTimeout` + `abort` + `abortReason='timeout'` 模式。
6. **函数拆分检查**：检索长任务对话框操作函数，验证是否拆为 `closeDialog` 与 `resetState` 两个独立函数。
7. **onBeforeUnmount 检查**：检索 `onBeforeUnmount` 块，对照 `required_cleanup_targets` 验证清理完整性；检索 `addEventListener` 调用，验证函数引用是否保存。

## 正确示例

```ts
// ✅ 长任务轮询 UI 完整实现（FR-051-1/2/3/4/5/6）
import { ref, onBeforeUnmount } from 'vue'

// ✅ 五状态机驱动 UI（FR-051-1）
const videoState = ref<'idle' | 'queued' | 'processing' | 'completed' | 'failed'>('idle')
const errorMessage = ref('')
const videoTaskId = ref<string | null>(null)
const dialogVisible = ref(false)

// ✅ abortReason 三态管理（FR-051-4，与 FR-050-2 一致）
const abortReason = ref<'user' | 'timeout' | null>(null)
let abortController: AbortController | null = null
let pollTimer: ReturnType<typeof setInterval> | null = null
let timeoutTimer: ReturnType<typeof setTimeout> | null = null

// ✅ 保存监听器引用以便 onBeforeUnmount 清理（FR-051-6）
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') closeDialog()
}

async function createVideo(prompt: string) {
  videoState.value = 'queued'
  abortReason.value = null
  dialogVisible.value = true
  abortController = new AbortController()

  // ✅ 超时用 setTimeout 而非 AbortSignal.timeout（FR-051-4）
  timeoutTimer = setTimeout(() => {
    abortReason.value = 'timeout'  // ✅ 同步设标记
    abortController?.abort()
    stopPolling()
    videoState.value = 'failed'
    errorMessage.value = '生成超时，请重试'
  }, 300000)  // 从 config.long_task_polling_ui_frontend.timeout_ms 读取

  const res = await fetch('/api/media/video', {
    method: 'POST',
    body: JSON.stringify({ prompt }),
    signal: abortController.signal
  })
  const { taskId } = await res.json()
  videoTaskId.value = taskId
  videoState.value = 'processing'
  startPolling(taskId)
}

function startPolling(taskId: string) {
  // ✅ setInterval 轮询（FR-051-1）
  pollTimer = setInterval(() => pollStatus(taskId), 5000)  // 从 config.poll_interval_ms 读取
}

async function pollStatus(taskId: string) {
  try {
    const res = await fetch(`/api/media/video/${taskId}`)
    const data = await res.json()

    // ✅ 完成/失败显式停止定时器（FR-051-3）
    if (data.status === 'completed') {
      videoState.value = 'completed'
      stopPolling()
    } else if (data.status === 'failed') {
      videoState.value = 'failed'
      errorMessage.value = data.error || '生成失败'
      stopPolling()
    } else {
      videoState.value = data.status
    }
  } catch (err) {
    // ✅ 单次失败不终止，仅更新 error 文案（FR-051-2）
    errorMessage.value = '查询失败，重试中...'
    // ❌ 禁止：stopPolling()（会终止整个轮询）
  }
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  if (timeoutTimer) {
    clearTimeout(timeoutTimer)
    timeoutTimer = null
  }
}

// ✅ "关闭对话框"与"重置状态"拆为两个函数（FR-051-5）
function closeDialog() {
  stopPolling()
  abortController?.abort()
  dialogVisible.value = false
  // 重置全部状态
  videoState.value = 'idle'
  videoTaskId.value = null
  errorMessage.value = ''
  abortReason.value = null
}

function resetState() {
  stopPolling()
  abortController?.abort()
  // 保持对话框打开，仅清状态允许重新生成
  videoState.value = 'idle'
  videoTaskId.value = null
  errorMessage.value = ''
  abortReason.value = null
  // ❌ 禁止：dialogVisible.value = false（关闭对话框是 closeDialog 的职责）
}

// ✅ 用户主动停止（FR-051-4，与 FR-050-2 一致）
function stopByUser() {
  abortReason.value = 'user'  // ✅ 区分用户停止与超时
  abortController?.abort()
  stopPolling()
  videoState.value = 'failed'
  errorMessage.value = '已取消生成'
}

// ✅ onBeforeUnmount 清理三类资源（FR-051-6）
onBeforeUnmount(() => {
  // 1. 清理 abortController
  abortController?.abort()
  // 2. 清理定时器
  stopPolling()
  // 3. 清理 addEventListener（用保存的函数引用 remove）
  window.removeEventListener('keydown', handleKeydown)
})

// 注册监听器（函数引用已保存）
window.addEventListener('keydown', handleKeydown)
```

## 错误示例

```ts
// ❌ 仅 isLoading 布尔态，无状态机（FR-051-1 违规）
const isLoading = ref(false)
async function createVideo(prompt: string) {
  isLoading.value = true
  // ❌ 用户无法区分"排队中"与"处理中"，无法在"完成"与"失败"时正确切换 UI
  await pollVideoStatus()
  isLoading.value = false
}

// ❌ 单次失败终止轮询（FR-051-2 违规）
async function pollStatus(taskId: string) {
  try {
    const res = await fetch(`/api/media/video/${taskId}`)
    // ...
  } catch (err) {
    errorMessage.value = '查询失败'
    clearInterval(pollTimer)  // ❌ 网络抖动即终止，用户需手动重启
  }
}

// ❌ 完成/失败未显式停止定时器（FR-051-3 违规）
async function pollStatus(taskId: string) {
  const res = await fetch(`/api/media/video/${taskId}`)
  const data = await res.json()
  if (data.status === 'completed') {
    videoState.value = 'completed'
    // ❌ 未 clearInterval，组件未卸载时持续轮询已完成任务
  }
}

// ❌ 超时用 AbortSignal.timeout（FR-051-4 违规）
async function createVideo(prompt: string) {
  abortController = new AbortController()
  // ❌ AbortSignal.timeout 触发 abort 时无法同步设 abortReason
  // ❌ 调用方 catch 中无法区分"超时"与"用户停止"（都抛 AbortError）
  const res = await fetch('/api/media/video', {
    signal: AbortSignal.timeout(300000)  // ❌ 应改为 setTimeout
  })
}

// ❌ 关闭/重置合为一个函数（FR-051-5 违规）
function handleClose(keepOpen: boolean) {
  stopPolling()
  abortController?.abort()
  if (!keepOpen) {
    dialogVisible.value = false
  }
  videoState.value = 'idle'
  // ❌ 调用方易传错参数，且 keepOpen=true 时需额外手动管理对话框
}
// 调用：handleClose(false)  // ❌ 语义不清

// ❌ onBeforeUnmount 未清理所有资源（FR-051-6 违规）
onBeforeUnmount(() => {
  clearInterval(pollTimer)
  // ❌ 未 abortController.abort()，进行中请求飞溅
  // ❌ 未 removeEventListener，监听器残留
})
```

## 与其他规则的关系

- **FR-048（长短任务架构分离）**：FR-048-1 决定走轮询架构，FR-051 约束轮询 UI 的实现细节。两者互补：FR-048 是架构选择，FR-051 是 UI 实现。
- **FR-050（SSE 流消费错误处理）**：FR-050-2 的 abortReason 三态与 FR-051-4 的 abortReason 三态一致，SSE 流与轮询任务共用停止原因管理逻辑。
- **FR-052（事件委托 + 生命周期清理）**：FR-051-6 的 onBeforeUnmount 清理与 FR-052-3/4 的监听器清理互补——FR-051-6 关注轮询资源清理，FR-052 关注事件委托监听器清理。
- **AR-3（定时器清理）**：AR-3 通用约束定时器在 onBeforeUnmount 清理，FR-051-6 细化为长任务轮询的三类资源（abortController + 监听器 + 定时器）清理。

## 适配新项目

- **React / Next.js**：`ref` 改为 `useState` / `useRef`；`onBeforeUnmount` 改为 `useEffect` cleanup；`setInterval` / `setTimeout` 清理逻辑不变；状态机用 useState 管理。
- **Vue 2**：`ref` 改为 `data()`；`onBeforeUnmount` 改为 `beforeDestroy`；其余规则不变。
- **纯 JavaScript**：去掉 TypeScript 类型注解，状态机与清理逻辑不变。
- **RxJS 项目**：`setInterval` 改为 `timer(0, poll_interval_ms)` / `interval(poll_interval_ms)`；`clearInterval` 改为 `subscription.unsubscribe()`；状态机与 abortReason 逻辑不变。
- **React Query / SWR 项目**：`setInterval` 轮询改为 `useQuery({ refetchInterval: poll_interval_ms })`；状态机从 query.data 推导；abortReason 用 query 状态映射；onBeforeUnmount 清理由库自动处理。
