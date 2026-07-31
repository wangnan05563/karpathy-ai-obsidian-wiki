# SSE 事件对象映射分发（前端视角）（FR-049）

> 复盘来源：v3 媒体生成工具的 Query.vue 中 SSE 事件处理最初用 if/else if 链分发 answer / refs / image / ppt / video / done / error 等事件，SonarQube S3776 认知复杂度超标且新增事件类型需修改分发链路；后改为 `Record<string, Handler>` 对象映射表，新增事件只需追加键值对。同时 outputMode（结构模式）与 outputModes（事件可见性）初期混用导致 UI 错乱，后正交分离。
> 所有可变参数从 config/review-config.md 的 `sse_event_dispatch_frontend` 字段读取，禁止在规则文件中硬编码事件类型名或阈值。

## 规则

### FR-049-1：前端 SSE 事件处理器事件类型 ≥ 阈值时必须用对象映射表，禁止 if/else if 链

- **Severity**: critical
- **Description**：前端 SSE 事件处理器（`consumeSSEStream` 回调 / `EventSource.onmessage` 分支）当事件类型数 ≥ `sse_event_dispatch_frontend.object_dispatch_threshold`（默认 3）时，必须用 `Record<string, Handler>` 对象映射表替代 if/else if 链。对象映射表的优势：①新增事件类型只需追加键值对，不修改分发逻辑 ②SonarQube S3776 认知复杂度 < 15 ③事件类型可枚举为联合字面量类型，编译期检查缺失 handler。
- **判定标准**：检索 SSE 事件处理代码，若 `if (event.type === 'xxx')` / `switch (event.type)` 的分支数 ≥ `object_dispatch_threshold`，即视为违规。修复方式：重构为 `const handlers: Record<string, Handler> = { answer: handleAnswer, refs: handleRefs, ... }`，调用 `handlers[event.type]?.(event.data)`。

### FR-049-2：outputMode 必须用 TypeScript 联合字面量类型，禁止 string 或枚举

- **Severity**: critical
- **Description**：outputMode（输出结构模式，如 `'normal' | 'mindmap' | 'image' | 'ppt'`）必须用 TypeScript 联合字面量类型声明，禁止用 `string` 或 `enum`。联合字面量类型的优势：①新增模式追加字面量不破坏旧客户端（向后兼容）②编译期穷尽性检查（switch 分支缺失时 tsc 报错）③IDE 自动补全。
- **判定标准**：检索 outputMode 类型声明，若为 `string` / `enum OutputMode` / `type OutputMode = string`，即视为违规。修复方式：改为 `type OutputMode = 'normal' | 'mindmap' | 'image' | 'ppt'`。

### FR-049-3：outputMode（结构模式）与 outputModes（事件可见性）必须正交分离，禁止混用

- **Severity**: critical
- **Description**：`outputMode`（单个值，决定整体渲染结构，如 `image` 模式渲染图片卡片）与 `outputModes`（数组/集合，决定哪些 SSE 事件类型对用户可见，如 `['answer', 'image']`）语义正交，必须独立管理，禁止用一个字段兼任两种职责。混用会导致：切换结构模式误改事件可见性，或反之。
- **判定标准**：检索 outputMode / outputModes 的赋值与消费代码，若存在 `outputMode = 'image'` 同时隐式设置 `outputModes = ['image']`（或反向），即视为违规。修复方式：两个字段独立赋值，UI 渲染逻辑读 outputMode 决定结构，事件过滤逻辑读 outputModes 决定可见性。

### FR-049-4：未知事件类型必须有 default handler，禁止静默吞掉

- **Severity**: warning
- **Description**：对象映射表分发时，未知事件类型（`handlers[event.type]` 为 undefined）必须有 default handler 行为：至少 `console.warn` 记录未知事件名，禁止静默吞掉（否则后端新增事件类型前端无感知，调试困难）。default handler 行为由 `sse_event_dispatch_frontend.unknown_event_strategy`（默认 `warn`）决定。
- **判定标准**：检索对象映射表调用代码，若 `handlers[event.type]?.(data)` 无 fallback 处理（`??` / `||` / `if (!handler)` 分支），即视为违规。修复方式：`(handlers[event.type] ?? defaultHandler)(data)`，defaultHandler 至少 `console.warn`。

### FR-049-5：事件 handler 必须为独立函数引用，禁止内联箭头函数堆叠

- **Severity**: warning
- **Description**：对象映射表的 handler 必须为独立具名函数引用（`{ answer: handleAnswer }`），禁止内联箭头函数堆叠（`{ answer: (data) => { ... } }`）。独立函数引用的优势：①可单独单元测试 ②可复用 ③对象映射表声明简洁，一目了然事件类型清单。
- **判定标准**：检索对象映射表声明，若 handler 值为内联箭头函数且函数体 > `sse_event_dispatch_frontend.inline_threshold_lines`（默认 3 行），即视为违规。修复方式：抽为具名函数后引用。

## 适用场景

- Vue 3 / React 项目中消费 SSE 流式接口（`EventSource` / `fetch` + `ReadableStream`）。
- SSE 事件类型 ≥ 3 种的流式接口（LLM 查询返回 answer/refs/done/error 等）。
- 多模态输出场景（outputMode 切换 normal/mindmap/image/ppt 等结构模式）。

## 不适用场景

- SSE 事件类型 ≤ 2 种的简单流（if/else 可读性更好）。
- WebSocket 全双工通信（消息分发机制不同，但可参考本规则的对象映射模式）。
- 静态事件处理（编译期已确定所有事件类型，无运行时新增风险）。
- 单元测试中的 mock 事件处理（测试本身验证分发逻辑）。

## 检查流程

```
[开始] 扫描 .vue / .ts 文件中的 SSE 事件处理代码
  │
  ▼
[1] 对象映射表检查（FR-049-1）
  │  └─ 检索 consumeSSEStream / EventSource / onmessage 调用
  │       └─ 定位事件分发逻辑（if/else if 链 / switch / 对象映射表）
  │            └─ 分支数 ≥ object_dispatch_threshold 且用 if/else if → 标记违规
  │            └─ 分支数 ≥ object_dispatch_threshold 且用 switch → 标记违规
  │            └─ 用 Record<string, Handler> 对象映射表 → 合规
  │
  ▼
[2] outputMode 类型检查（FR-049-2）
  │  └─ 检索 outputMode 类型声明
  │       └─ string / enum / type = string → 标记违规
  │       └─ 联合字面量类型（'a' | 'b' | 'c'） → 合规
  │
  ▼
[3] 正交分离检查（FR-049-3）
  │  └─ 检索 outputMode 与 outputModes 的赋值点
  │       └─ 一个赋值同时影响两者 → 标记违规
  │       └─ 两者独立赋值 → 合规
  │
  ▼
[4] default handler 检查（FR-049-4）
  │  └─ 检索对象映射表调用（handlers[event.type]）
  │       └─ 无 ?? / || / if (!handler) fallback → 标记违规
  │
  ▼
[5] handler 引用方式检查（FR-049-5）
  │  └─ 检索对象映射表声明
  │       └─ handler 值为内联箭头函数且函数体 > inline_threshold_lines → 标记违规
  │
  ▼
[结束] 输出审查报告
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `sse_event_dispatch_frontend.enabled` | `true` | 是否启用 SSE 事件分发审查 |
| `sse_event_dispatch_frontend.object_dispatch_threshold` | `3` | 事件类型数 ≥ 此值时必须用对象映射表 |
| `sse_event_dispatch_frontend.known_event_types` | `answer, refs, done, error, progress, page, image, ppt, video, fixing, fixed` | 已知 SSE 事件类型清单（逗号分隔，用于 default handler 告警提示） |
| `sse_event_dispatch_frontend.unknown_event_strategy` | `warn` | 未知事件处理策略（`warn`=console.warn / `throw`=抛错 / `ignore`=静默，默认 warn） |
| `sse_event_dispatch_frontend.output_mode_field` | `outputMode` | 结构模式字段名 |
| `sse_event_dispatch_frontend.output_modes_field` | `outputModes` | 事件可见性字段名 |
| `sse_event_dispatch_frontend.allowed_output_modes` | `normal, mindmap, image, ppt` | 允许的 outputMode 联合字面量值（逗号分隔） |
| `sse_event_dispatch_frontend.inline_threshold_lines` | `3` | 内联箭头函数函数体行数上限，超过即须抽为具名函数 |
| `sse_event_dispatch_frontend.sonarqube_complexity_threshold` | `15` | SonarQube S3776 认知复杂度阈值，对象映射表应低于此值 |

## 检查方式

1. **SSE 消费点扫描**：在 `.vue` / `.ts` 文件中检索 `consumeSSEStream` / `EventSource` / `onmessage` / `addEventListener('message'`，定位事件分发代码。
2. **分发结构判定**：对每个分发点，统计分支数（if/else if 链的 else if 数 / switch 的 case 数），与 `object_dispatch_threshold` 比对。
3. **outputMode 类型核对**：检索 `type OutputMode` / `interface OutputMode` / `outputMode:` 类型声明，验证是否为联合字面量。
4. **正交分离验证**：检索 `outputMode` 与 `outputModes` 的赋值点，检查是否存在一个赋值同时影响两者。
5. **default handler 检查**：检索 `handlers[event.type]` / `handlers[type]` 调用，验证是否有 fallback 处理。
6. **handler 引用方式检查**：检索对象映射表声明，统计内联箭头函数函数体行数。

## 正确示例

```ts
// ✅ 对象映射表分发（FR-049-1）+ default handler（FR-049-4）
import type { SSEEvent } from '@/types/sse'

// ✅ handler 为独立具名函数引用（FR-049-5）
function handleAnswer(data: string) {
  answer.value += data
}
function handleRefs(data: RefsPayload) {
  refs.value = data.refs
}
function handleImage(data: ImagePayload) {
  images.value.push(data.url)
}
function handlePpt(data: PptPayload) {
  pptContent.value = data.content
}
function handleDone() {
  isStreaming.value = false
}
function handleError(data: ErrorPayload) {
  errorMessage.value = data.message
}

// ✅ 对象映射表替代 if/else if 链（FR-049-1）
const handlers: Record<string, (data: any) => void> = {
  answer: handleAnswer,
  refs: handleRefs,
  image: handleImage,
  ppt: handlePpt,
  done: handleDone,
  error: handleError
}

// ✅ default handler：未知事件 console.warn（FR-049-4）
function defaultHandler(data: any, eventType: string) {
  console.warn(`[SSE] 未知事件类型: ${eventType}`, data)
}

function dispatchEvent(event: SSEEvent) {
  // ✅ 用 ?? 提供 default handler（FR-049-4）
  const handler = handlers[event.type] ?? ((data: any) => defaultHandler(data, event.type))
  handler(event.data)
}
```

```ts
// ✅ outputMode 联合字面量类型（FR-049-2）+ outputModes 正交分离（FR-049-3）
import type { SSEEvent } from '@/types/sse'

// ✅ outputMode 用联合字面量类型（FR-049-2）
type OutputMode = 'normal' | 'mindmap' | 'image' | 'ppt'

// ✅ outputMode（结构模式）与 outputModes（事件可见性）正交分离（FR-049-3）
const outputMode = ref<OutputMode>('normal')        // 决定渲染结构
const outputModes = ref<string[]>(['answer', 'refs']) // 决定事件可见性

// ✅ 切换结构模式不影响事件可见性（FR-049-3）
function switchOutputMode(mode: OutputMode) {
  outputMode.value = mode
  // ❌ 禁止：outputModes.value = [mode]（混用）
  // ✅ outputModes 独立管理
}

// ✅ 切换事件可见性不影响结构模式（FR-049-3）
function toggleEventVisibility(eventType: string) {
  const idx = outputModes.value.indexOf(eventType)
  if (idx >= 0) {
    outputModes.value.splice(idx, 1)
  } else {
    outputModes.value.push(eventType)
  }
  // ❌ 禁止：outputMode.value = eventType（混用）
}

// 渲染时读 outputMode 决定结构
const renderComponent = computed(() => {
  switch (outputMode.value) {
    case 'normal': return NormalOutput
    case 'mindmap': return MindmapOutput
    case 'image': return ImageOutput
    case 'ppt': return PptOutput
  }
})

// 事件过滤读 outputModes 决定可见性
function isEventVisible(eventType: string): boolean {
  return outputModes.value.includes(eventType)
}
```

## 错误示例

```ts
// ❌ if/else if 链分发 6 种事件（FR-049-1 违规，认知复杂度超标）
function dispatchEvent(event: SSEEvent) {
  if (event.type === 'answer') {
    answer.value += event.data
  } else if (event.type === 'refs') {
    refs.value = event.data.refs
  } else if (event.type === 'image') {
    images.value.push(event.data.url)
  } else if (event.type === 'ppt') {
    pptContent.value = event.data.content
  } else if (event.type === 'done') {
    isStreaming.value = false
  } else if (event.type === 'error') {
    errorMessage.value = event.data.message
  }
  // ❌ 新增事件类型需修改分发链路，认知复杂度持续增长
  // ❌ 无 default handler，未知事件被静默吞掉（FR-049-4 违规）
}

// ❌ outputMode 用 string 类型（FR-049-2 违规）
type OutputMode = string  // ❌ 失去编译期穷尽性检查
const outputMode = ref<OutputMode>('normal')
// 任意字符串都可赋值，拼写错误不报错
outputMode.value = 'imag'  // ❌ 拼写错误，运行时才发现

// ❌ outputMode 与 outputModes 混用（FR-049-3 违规）
function switchToImageMode() {
  outputMode.value = 'image'
  outputModes.value = ['image']  // ❌ 切换结构模式误改事件可见性
  // 用户切换 image 模式后，answer 事件不再可见，无法看到 LLM 文本
}

// ❌ 对象映射表无 default handler（FR-049-4 违规）
function dispatchEvent(event: SSEEvent) {
  const handler = handlers[event.type]
  handler?.(event.data)  // ❌ 未知事件被静默吞掉，无 console.warn
}

// ❌ handler 内联箭头函数堆叠（FR-049-5 违规）
const handlers = {
  answer: (data: string) => {
    answer.value += data
    // ... 10 行逻辑 ...
    // ❌ 无法单独单元测试
    // ❌ 对象映射表声明臃肿，事件类型清单不清晰
  },
  refs: (data: RefsPayload) => {
    refs.value = data.refs
    // ... 8 行逻辑 ...
  }
}
```

## 与其他规则的关系

- **FR-048（长短任务架构分离）**：FR-048-1 决定任务走 SSE 流后，FR-049 约束 SSE 事件的前端分发方式。两者互补：FR-048 是架构选择，FR-049 是事件分发实现。
- **FR-050（SSE 流消费错误处理）**：FR-049 约束事件分发结构，FR-050 约束流消费的错误处理（AbortError 吞掉、reader.cancel 兜底）。两者共同覆盖 SSE 流消费的前端实现。
- **FR-028（混合类型运行时分流）**：outputMode 联合字面量类型的消费（switch 分支）受 FR-028 穷尽性分支约束；FR-049-2 约束类型声明形式，FR-028 约束消费方式。
- **AR-2（SSE 心跳与重连）**：AR-2 约束 SSE 连接层的心跳与重连，FR-049 约束 SSE 事件层的分发结构，两者分属不同层次。

## 适配新项目

- **React / Next.js**：`ref<OutputMode>` 改为 `useState<OutputMode>`；`computed` 改为 `useMemo`；对象映射表模式不变；事件 handler 独立函数引用不变。
- **Vue 2**：`ref` 改为 `data()` + `this.$set`；`computed` 语法不变；对象映射表模式不变。
- **纯 JavaScript**：去掉 TypeScript 类型注解（联合字面量类型改为 JSDoc `@typedef`），对象映射表与 default handler 逻辑不变。
- **WebSocket 项目**：消息分发同样适用对象映射表模式，`event.type` 改为 `message.type` 或自定义消息协议字段。
- **GraphQL Subscription 项目**：事件分发改为 subscription message 分发，对象映射表模式不变，事件类型从 GraphQL schema 推导。
