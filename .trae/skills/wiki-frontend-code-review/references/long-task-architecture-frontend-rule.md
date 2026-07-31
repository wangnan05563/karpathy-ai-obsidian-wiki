# 长短任务架构分离（前端视角）（FR-048）

> 复盘来源：v3 媒体生成工具开发中，视频生成任务耗时分钟级，初期误用 SSE 流承载导致连接超时断开、用户无法获知进度；后改为"POST 创建任务返回 taskId + GET 轮询状态"的独立 JSON 端点架构，前端按 HTTP 状态码区分配置缺失（400）与外部 API 失败（500），按 429 反馈限流。前端视角关注：①根据任务预估耗时选择 SSE 流 vs 独立端点轮询 ②HTTP 状态码分类驱动 UI 反馈 ③限流反馈与重试策略。
> 所有可变参数从 config/review-config.md 的 `long_task_architecture_frontend` 字段读取，禁止在规则文件中硬编码超时阈值、状态码或端点路径。

## 规则

### FR-048-1：前端必须按任务预估耗时选择 SSE 流或独立端点轮询，禁止分钟级任务走 SSE

- **Severity**: critical
- **Description**：前端发起任务请求前，必须按 `long_task_architecture_frontend.sse_threshold_ms`（默认 30000ms）判定任务架构：预估耗时 ≤ 阈值走 SSE 流（`text/event-stream` 同步消费），预估耗时 > 阈值走独立 JSON 端点（POST 创建任务返回 taskId + GET 轮询）。禁止将分钟级任务（如视频生成、批量处理）塞进 SSE 流——SSE 连接易因代理超时、网络抖动断开，且无法承载轮询节奏。
- **判定标准**：检索前端任务调用代码，若任务名 ∈ `long_task_architecture_frontend.long_task_names`（默认 `video, batch, podcast`）却用 `EventSource` / `consumeSSEStream` 消费，即视为违规。修复方式：改为 POST 创建 + GET 轮询架构（参见 FR-051 长任务轮询 UI 模式）。

### FR-048-2：HTTP 状态码必须分类驱动 UI 反馈，禁止统一"后端服务未运行"提示

- **Severity**: critical
- **Description**：前端接收任务端点响应时，必须按 `long_task_architecture_frontend.status_code_strategy`（默认映射表）分类处理：
  - `400` → 配置缺失分支：引导用户前往配置页（`config_redirect_message`），不提示"服务错误"
  - `500` → 外部 API 失败分支：提示重试（`external_failure_message`），不引导配置
  - `429` → 限流分支：提示稍后重试（`rate_limit_message`），按 `retry_after_header` 读取等待秒数
  - `5xx`（非 500）→ 服务异常分支：提示服务暂不可用（`service_unavailable_message`）
- **判定标准**：检索前端 fetch/axios 调用的 catch 或 response 处理，若所有非 2xx 状态码统一走同一错误文案（尤其是硬编码"后端服务未运行"），即视为违规。修复方式：按状态码分流，每类状态码绑定对应的 UI 反馈动作。

### FR-048-3：SSE 流任务必须在 finally 中清理 reader，独立端点任务必须暴露取消方法

- **Severity**: critical
- **Description**：SSE 流任务必须在 `finally` 块中调用 `reader.cancel()` 兜底释放（与 FR-050 互补）；独立端点轮询任务必须暴露 `cancel()` 方法供调用方主动停止轮询（清理 `setInterval` + 标记 `aborted`）。两种架构的清理路径不同但都不可缺。
- **判定标准**：SSE 流任务无 finally 清理（参见 FR-050）；独立端点轮询任务无 `cancel()` / `stop()` 方法导出，即视为违规。修复方式：补齐对应的清理逻辑。

### FR-048-4：任务端点调用必须区分"创建"与"查询"语义，禁止 GET 触发外部 API 成本

- **Severity**: warning
- **Description**：前端调用任务端点时，必须区分语义：创建任务（触发 LLM/外部 API 成本）用 POST，查询任务状态（无副作用）用 GET。禁止用 GET 触发外部 API 成本（违反 HTTP 语义 + 无法被限流中间件正确拦截）。
- **判定标准**：检索前端任务调用代码，若创建任务用 GET 或查询状态用 POST，即视为违规。修复方式：调整为 POST 创建 + GET 查询。

## 适用场景

- Vue 3 / React 项目中调用后端任务端点（LLM 查询、媒体生成、批量处理等）。
- 任务耗时跨度大（秒级 LLM 查询 + 分钟级视频生成共存的系统）。
- 需要区分配置错误与外部服务错误的前端交互场景。

## 不适用场景

- 纯前端计算任务（无后端调用，如本地 Canvas 渲染）。
- 静态资源请求（图片、CSS、JS chunk 加载）。
- WebSocket 全双工通信场景（架构不同，参见 WebSocket 专属规则）。
- 单元测试中的 mock 调用（测试本身验证调用逻辑，无需架构判定）。

## 检查流程

```
[开始] 扫描 .vue / .ts 文件中的任务调用代码
  │
  ▼
[1] 任务架构选择检查（FR-048-1）
  │  └─ 检索任务名是否 ∈ long_task_names 列表
  │       └─ 命中 long_task_names 却用 EventSource / consumeSSEStream → 标记违规
  │       └─ 未命中 long_task_names 且耗时 ≤ sse_threshold_ms → 走 SSE（合规）
  │       └─ 命中 long_task_names → 走 POST + GET 轮询（合规）
  │
  ▼
[2] 状态码分类检查（FR-048-2）
  │  └─ 定位 fetch / axios 的 response 或 catch 处理
  │       └─ 检查 status_code_strategy 中各状态码是否有对应分支
  │            └─ 统一文案 / 硬编码"后端服务未运行" → 标记违规
  │
  ▼
[3] 清理路径检查（FR-048-3）
  │  └─ SSE 流任务：检查 finally 块是否有 reader.cancel()
  │       └─ 无 finally 清理 → 标记违规（转 FR-050 详情）
  │  └─ 轮询任务：检查是否导出 cancel() / stop() 方法
  │       └─ 无取消方法 → 标记违规
  │
  ▼
[4] HTTP 语义检查（FR-048-4）
  │  └─ 创建任务用 GET 或查询用 POST → 标记违规
  │
  ▼
[结束] 输出审查报告
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `long_task_architecture_frontend.sse_threshold_ms` | `30000` | SSE 流与独立端点的耗时分界（毫秒） |
| `long_task_architecture_frontend.long_task_names` | `video, batch, podcast` | 长任务名清单（逗号分隔，强制走独立端点） |
| `long_task_architecture_frontend.short_task_names` | `query, search, summarize` | 短任务名清单（逗号分隔，走 SSE） |
| `long_task_architecture_frontend.status_code_strategy` | `400=config_redirect, 500=external_retry, 429=rate_limit_wait, 5xx=service_unavailable` | 状态码 → UI 反馈策略映射 |
| `long_task_architecture_frontend.config_redirect_message` | `配置缺失，请前往配置页设置` | 400 状态码的引导文案 |
| `long_task_architecture_frontend.external_failure_message` | `外部服务调用失败，请重试` | 500 状态码的重试文案 |
| `long_task_architecture_frontend.rate_limit_message` | `操作过于频繁，请稍后重试` | 429 状态码的限流文案 |
| `long_task_architecture_frontend.service_unavailable_message` | `服务暂不可用，请稍后重试` | 5xx 状态码的异常文案 |
| `long_task_architecture_frontend.retry_after_header` | `Retry-After` | 429 响应中读取等待秒数的 header 名 |
| `long_task_architecture_frontend.create_method` | `POST` | 创建任务的 HTTP 方法 |
| `long_task_architecture_frontend.query_method` | `GET` | 查询任务状态的 HTTP 方法 |

## 检查方式

1. **任务名扫描**：在 `.vue` / `.ts` 文件中检索 `long_task_names` 与 `short_task_names` 中的任务名，定位调用点。
2. **架构判定**：对每个任务调用，检查是否用 `EventSource` / `consumeSSEStream`（SSE 流）或 `fetch` / `axios`（独立端点），与任务名所属分类比对。
3. **状态码分支检查**：检索 fetch/axios 的 `.catch()` / `response.status` 处理，对照 `status_code_strategy` 验证各状态码是否有独立分支。
4. **文案硬编码扫描**：检索错误处理分支是否硬编码"后端服务未运行"等统一文案。
5. **清理路径检查**：SSE 流任务检查 finally 块；轮询任务检查 cancel/stop 方法导出。
6. **HTTP 方法核对**：创建任务端点检查是否用 `create_method`，查询端点检查是否用 `query_method`。

## 正确示例

```ts
// ✅ 视频生成（长任务）走独立端点 + 轮询（FR-048-1）
import { ref, onBeforeUnmount } from 'vue'

const videoState = ref<'idle' | 'queued' | 'processing' | 'completed' | 'failed'>('idle')
const videoTaskId = ref<string | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

// ✅ 创建任务用 POST（FR-048-4）
async function createVideo(prompt: string) {
  const res = await fetch('/api/media/video', {
    method: 'POST',  // 从 config.long_task_architecture_frontend.create_method 读取
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt })
  })

  // ✅ 状态码分类驱动 UI 反馈（FR-048-2）
  if (res.status === 400) {
    // 配置缺失：引导用户前往配置页
    ElMessage.warning('配置缺失，请前往配置页设置')
    return
  } else if (res.status === 429) {
    // 限流：读取 Retry-After header
    const retryAfter = res.headers.get('Retry-After') || '60'
    ElMessage.warning(`操作过于频繁，请 ${retryAfter} 秒后重试`)
    return
  } else if (res.status === 500) {
    // 外部 API 失败：提示重试
    ElMessage.error('外部服务调用失败，请重试')
    return
  } else if (!res.ok) {
    ElMessage.error('服务暂不可用，请稍后重试')
    return
  }

  const { taskId } = await res.json()
  videoTaskId.value = taskId
  videoState.value = 'queued'
  startPolling(taskId)
}

// ✅ 查询任务状态用 GET（FR-048-4）
async function pollVideoStatus(taskId: string) {
  const res = await fetch(`/api/media/video/${taskId}`, { method: 'GET' })
  const data = await res.json()
  videoState.value = data.status
}

// ✅ 暴露 cancel() 方法供调用方主动停止（FR-048-3）
function cancelVideoPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  videoTaskId.value = null
}

function startPolling(taskId: string) {
  pollTimer = setInterval(() => pollVideoStatus(taskId), 5000)
}

// ✅ onBeforeUnmount 清理（FR-048-3）
onBeforeUnmount(() => cancelVideoPolling())
```

```ts
// ✅ LLM 查询（短任务）走 SSE 流（FR-048-1）
async function queryLLM(prompt: string, signal?: AbortSignal) {
  const res = await fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
    signal
  })

  const reader = res.body!.getReader()
  try {
    // SSE 流消费（详见 FR-050 SSE 流消费错误处理）
    await consumeSSEStream(reader, handleEvent, signal)
  } catch (err) {
    if ((err as Error).name === 'AbortError') return  // 用户主动停止
    // 按状态码分类处理（FR-048-2）
    ElMessage.error('查询失败，请重试')
  } finally {
    // ✅ SSE 流任务在 finally 清理 reader（FR-048-3）
    reader.cancel().catch(() => {})
  }
}
```

## 错误示例

```ts
// ❌ 视频生成（长任务）误用 SSE 流（FR-048-1 违规）
async function generateVideo(prompt: string) {
  // 视频生成为分钟级任务，SSE 流易超时断开
  const eventSource = new EventSource(`/api/media/video?prompt=${prompt}`)
  eventSource.onmessage = (e) => {
    // SSE 流无法承载分钟级任务的轮询节奏
    console.log(e.data)
  }
}

// ❌ 所有错误统一"后端服务未运行"（FR-048-2 违规）
async function createVideo(prompt: string) {
  try {
    const res = await fetch('/api/media/video', { method: 'POST', body: JSON.stringify({ prompt }) })
    if (!res.ok) {
      // 硬编码统一文案，无法区分配置缺失 vs 外部失败
      ElMessage.error('后端服务未运行')
      return
    }
  } catch (e) {
    ElMessage.error('后端服务未运行')  // ❌ 网络错误也归为"服务未运行"
  }
}

// ❌ 轮询任务未暴露 cancel() 方法（FR-048-3 违规）
function startVideoPolling(taskId: string) {
  setInterval(() => pollVideoStatus(taskId), 5000)
  // ❌ 未导出 cancel()，调用方无法主动停止轮询
  // ❌ onBeforeUnmount 无法清理定时器 → 内存泄漏
}

// ❌ 创建任务用 GET（FR-048-4 违规）
async function createVideo(prompt: string) {
  // GET 触发外部 API 成本，违反 HTTP 语义 + 限流中间件无法正确拦截
  const res = await fetch(`/api/media/video?prompt=${prompt}`)  // ❌ 应为 POST
}
```

## 与其他规则的关系

- **FR-050（SSE 流消费错误处理）**：FR-048-1 决定任务走 SSE 还是轮询，FR-050 约束 SSE 流的具体错误处理（AbortError 吞掉、reader.cancel 兜底）。两者互补：FR-048 是架构选择，FR-050 是实现细节。
- **FR-051（长任务轮询 UI 模式）**：FR-048-1 决定走轮询架构，FR-051 约束轮询 UI 的状态机、定时器清理、abortReason 三态等实现细节。
- **AR-1~AR-4（Async 可靠性）**：FR-048-2 的状态码分类与 AR-4 的降级 UI 反馈互补——AR-4 要求 async 失败有 UI 反馈，FR-048-2 细化反馈按状态码分流。
- **FR-049（SSE 事件对象映射分发）**：FR-048-1 决定走 SSE 流后，FR-049 约束 SSE 事件的分发方式（对象映射表替代 if/else 链）。

## 适配新项目

- **React / Next.js**：`EventSource` 改为 `fetch` + `ReadableStream` 消费；`ElMessage` 改为 `toast` / `sonner`；状态码分流逻辑不变；`onBeforeUnmount` 改为 `useEffect` cleanup。
- **Vue 2**：`onBeforeUnmount` 改为 `beforeDestroy` / `beforeUnmount`；其余规则不变。
- **纯 JavaScript**：去掉 TypeScript 类型注解，状态码分流与清理逻辑不变。
- **GraphQL 项目**：长任务改为 mutation（创建）+ subscription（状态推送）+ query（查询）组合；状态码分流改为 GraphQL error code 分流。
- **微服务架构**：任务创建与查询可能走不同服务，`create_endpoint` 与 `query_endpoint_template` 从 config 读取对应服务路径。
