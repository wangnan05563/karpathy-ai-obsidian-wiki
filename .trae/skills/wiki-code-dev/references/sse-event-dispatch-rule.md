# SSE 事件对象映射分发规则（CODING-063）

> 复盘来源：v3 媒体生成工具开发中，SSE 后端事件分发用 if/else 链（`if (chunk.text) ... else if (chunk.image) ... else if (chunk.ppt) ...`），新增事件类型需修改多处分支；前端 SSE 事件处理器同样用 if/else 链，SonarQube S3776 报认知复杂度 > 15。改用对象映射表 `Record<string, Handler>` 替代，新增事件类型只需追加一行映射。同时 outputMode 用 TypeScript 联合字面量类型，新增模式追加字面量不破坏旧客户端。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `sse_event` 字段读取，禁止在规则文件中硬编码复杂度阈值。

## 规则

**SSE 事件分发（后端）与消费（前端）必须遵守五项契约**：

1. **后端按字段独立 if 分发**：后端按 chunk 字段独立 `if (chunk.image) send('image', chunk.image)` 分发，新增事件类型只需追加 if 分支（无需修改 else 链）
2. **前端对象映射表**：前端 SSE 事件处理器用对象映射表 `Record<string, Handler>` 替代 if/else 链，控制 SonarQube S3776 认知复杂度 < `sse_event.object_dispatch_threshold`（默认 15）
3. **outputMode 联合字面量类型**：outputMode 用 TypeScript 联合字面量类型（`'normal' | 'mindmap' | 'image' | 'ppt'`），新增模式追加字面量不破坏旧客户端
4. **outputMode 与 outputModes 正交分离**：`outputMode`（结构模式，决定渲染组件）与 `outputModes`（事件可见性，决定哪些事件可见）正交分离，不可混用
5. **未知事件默认 handler**：未知事件类型的默认 handler 行为必须明确（如 `console.warn`），禁止静默吞掉

## 适用场景

- SSE 流式响应（LLM 流式输出、媒体生成进度、长任务状态推送）
- 多事件类型的 WebSocket / SSE 消息分发
- 事件类型会持续扩展的场景（用对象映射表降低修改成本）
- 需要类型安全的事件处理（TypeScript 联合字面量类型）

## 不适用场景

- 单事件类型的简单 SSE（无需对象映射，直接处理即可）
- 事件类型固定不变的场景（if/else 可读性更高）
- 非 TypeScript 项目（无联合字面量类型，用字符串常量替代）
- 一次性脚本（无需可扩展性）

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `sse_event.enabled` | `true` | 是否启用 SSE 事件分发守卫 |
| `sse_event.severity` | `error` | 违规严重级别 |
| `sse_event.object_dispatch_threshold` | `3` | 事件类型 ≥ 此值时必须用对象映射表 |
| `sse_event.cognitive_complexity_limit` | `15` | SonarQube S3776 认知复杂度上限 |
| `sse_event.unknown_event_strategy` | `warn` | 未知事件处理策略（warn / error / ignore） |
| `sse_event.allowed_output_modes` | `normal,mindmap,image,ppt,video` | 允许的 outputMode 枚举 |

## 检查方式

1. **后端分发检查**：后端 SSE 流写入必须按字段独立 `if` 分发，禁止用 `if/else if/else` 链（else 会阻断新事件类型追加）
2. **前端映射表检查**：前端事件处理器事件类型 ≥ `object_dispatch_threshold` 时必须用 `Record<string, Handler>` 对象映射表
3. **认知复杂度检查**：前端事件处理函数的 SonarQube S3776 认知复杂度必须 < `cognitive_complexity_limit`
4. **类型检查**：outputMode 必须用 TypeScript 联合字面量类型，禁止用 `string` 泛型
5. **正交分离检查**：`outputMode` 与 `outputModes` 字段不得在同一处判断，前者决定渲染组件，后者决定事件可见性
6. **未知事件检查**：对象映射表必须含 default handler，按 `unknown_event_strategy` 处理未知事件

## 正确示例

```typescript
// services/api/src/routes/query.ts（后端 SSE 分发）
// ✅ 按字段独立 if 分发，新增事件类型只需追加 if 分支
async function sendSSEEvents(stream: ReadableStream, raw: FastifyReply['raw']) {
  const reader = stream.getReader();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = JSON.parse(value) as any;

    // ✅ 独立 if 分发，新增类型追加 if 即可
    if (chunk.text) raw.write(`event: text\ndata: ${JSON.stringify(chunk.text)}\n\n`);
    if (chunk.image) raw.write(`event: image\ndata: ${JSON.stringify(chunk.image)}\n\n`);
    if (chunk.ppt) raw.write(`event: ppt\ndata: ${JSON.stringify(chunk.ppt)}\n\n`);
    if (chunk.video) raw.write(`event: video\ndata: ${JSON.stringify(chunk.video)}\n\n`);
    if (chunk.error) raw.write(`event: error\ndata: ${JSON.stringify(chunk.error)}\n\n`);
  }
  raw.end();
}
```

```typescript
// frontend/src/stores/query.ts（前端对象映射表）
// ✅ outputMode 联合字面量类型
type OutputMode = 'normal' | 'mindmap' | 'image' | 'ppt' | 'video';

// ✅ 事件处理器对象映射表，控制认知复杂度
type SSEEventHandler = (data: any) => void;
const handlers: Record<string, SSEEventHandler> = {
  text: (data) => { appendText(data); },
  image: (data) => { setImageUrl(data); },
  ppt: (data) => { setPptContent(data); },
  video: (data) => { setVideoUrl(data); },
  error: (data) => { setError(data); },
};

async function consumeSSE(response: Response) {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.startsWith('event: ')) continue;
      const eventName = line.slice(7);
      const dataLine = lines[lines.indexOf(line) + 1];
      if (!dataLine?.startsWith('data: ')) continue;
      const data = JSON.parse(dataLine.slice(6));

      // ✅ 对象映射表分发，新增事件只需追加 handlers 一行
      const handler = handlers[eventName];
      if (handler) {
        handler(data);
      } else {
        // ✅ 未知事件默认 handler 行为明确
        console.warn(`[SSE] 未知事件类型: ${eventName}`);
      }
    }
  }
}
```

## 错误示例

```typescript
// ❌ 错误：后端用 if/else if/else 链，新增事件需修改 else 分支
if (chunk.text) {
  raw.write(`event: text\ndata: ${JSON.stringify(chunk.text)}\n\n`);
} else if (chunk.image) {
  raw.write(`event: image\ndata: ${JSON.stringify(chunk.image)}\n\n`);
} else {
  // ⚠️ 新增事件类型需修改此处 else，易遗漏
  raw.write(`event: unknown\ndata: ${JSON.stringify(chunk)}\n\n`);
}

// ❌ 错误：前端用 if/else if 链，认知复杂度高
async function consumeSSE(response: Response) {
  // ...
  if (eventName === 'text') {
    appendText(data);
  } else if (eventName === 'image') {
    setImageUrl(data);
  } else if (eventName === 'ppt') {
    setPptContent(data);
  } else if (eventName === 'video') {
    setVideoUrl(data);
  } else if (eventName === 'error') {
    setError(data);
  } else if (eventName === 'progress') {
    // ⚠️ SonarQube S3776 认知复杂度 > 15
  }
}

// ❌ 错误：outputMode 用 string 泛型，无类型安全
type OutputMode = string; // ⚠️ 应为联合字面量类型

// ❌ 错误：outputMode 与 outputModes 混用
function render(mode: string, visibleModes: string[]) {
  if (mode === 'image' && visibleModes.includes('image')) {
    // ⚠️ outputMode（结构模式）与 outputModes（事件可见性）正交，不应同处判断
  }
}

// ❌ 错误：未知事件静默吞掉
const handler = handlers[eventName];
if (handler) handler(data);
// ⚠️ 未知事件无任何处理，调试困难
```

## 适配新项目

- 适配 WebSocket：将 SSE 事件改为 WebSocket 消息，对象映射表结构不变
- 适配 Server-Sent Events polyfill：用 `EventSource` API，`addEventListener(eventName, handler)` 替代对象映射表
- 适配 gRPC streaming：将 chunk 字段改为 proto message oneof，对象映射表按 oneof case 分发
- 适配 React/Vue：对象映射表的 handler 改为 setState / ref 操作，配合框架响应式系统
- 适配非 TypeScript 项目：outputMode 联合字面量类型改为字符串常量 `const OUTPUT_MODES = ['normal', 'mindmap', ...] as const`

## 与其他规则的关系

- 与 CODING-064（SSE 流消费错误处理）联动：本规则的对象映射表中的 handler 必须吞掉 AbortError
- 与 CODING-059（长/短任务架构分离）联动：秒级任务走 SSE 时用本规则的事件分发模式
- 与 CODING-065（长任务轮询 UI 模式）联动：长任务不走 SSE，走独立端点 + 轮询，事件类型用状态机枚举
- 与 CODING-027（Composable API 先读后用）联动：调用第三方 SSE 库前必须 Read 源码确认其事件分发模式
- 与类型同步守卫（CODING-030）联动：outputMode 联合字面量类型必须前后端同步
