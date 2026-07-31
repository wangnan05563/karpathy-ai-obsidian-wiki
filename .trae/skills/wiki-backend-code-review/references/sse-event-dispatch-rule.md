# SSE 事件对象映射分发审查规则（BR-060）

> 复盘来源：v3 媒体生成工具开发中，SSE 后端事件分发用 if/else 链（`if (chunk.text) ... else if (chunk.image) ... else if (chunk.ppt) ...`），新增事件类型需修改多处分支；前端 SSE 事件处理器同样用 if/else 链，SonarQube S3776 报认知复杂度 > 15。改用对象映射表 `Record<string, Handler>` 替代，新增事件类型只需追加一行映射。同时 outputMode 用 TypeScript 联合字面量类型，新增模式追加字面量不破坏旧客户端（CODING-063）。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"SSE 事件对象映射分发审查参数（sse_event_dispatch）"章节读取，禁止在本规则文件硬编码复杂度阈值。

## Trigger Keywords

text/event-stream, reply.raw.write, event:, chunk.text, chunk.image, chunk.ppt, chunk.video, if/else if, else, Record<string, Handler>, handlers, outputMode, outputModes, 联合字面量, S3776, cognitive complexity, 未知事件, console.warn, default handler

## Rules

### BR-060-1：后端 SSE 事件分发必须用独立 if 分发，禁止 if/else if/else 链

- **Severity**: critical
- **Description**: 后端 SSE 流写入必须按 chunk 字段独立 `if (chunk.image) raw.write(...)` 分发，禁止用 `if/else if/else` 链。独立 if 分发新增事件类型只需追加 if 分支（无需修改 else 链）；if/else if/else 链新增事件需修改 else 分支，易遗漏。评审时确认：后端 SSE 分发代码用独立 if（无 else if / else），每个事件类型一个 if 分支。
- **Suggested fix**:

```typescript
// 错误：后端用 if/else if/else 链，新增事件需修改 else 分支
if (chunk.text) {
  raw.write(`event: text\ndata: ${JSON.stringify(chunk.text)}\n\n`);
} else if (chunk.image) {
  raw.write(`event: image\ndata: ${JSON.stringify(chunk.image)}\n\n`);
} else {
  raw.write(`event: unknown\ndata: ${JSON.stringify(chunk)}\n\n`); // ❌ 新增事件需修改此处
}

// 正确：独立 if 分发，新增类型追加 if 即可
if (chunk.text) raw.write(`event: text\ndata: ${JSON.stringify(chunk.text)}\n\n`); // ✅
if (chunk.image) raw.write(`event: image\ndata: ${JSON.stringify(chunk.image)}\n\n`); // ✅
if (chunk.ppt) raw.write(`event: ppt\ndata: ${JSON.stringify(chunk.ppt)}\n\n`); // ✅
if (chunk.video) raw.write(`event: video\ndata: ${JSON.stringify(chunk.video)}\n\n`); // ✅
```

### BR-060-2：前端 SSE 事件处理器事件类型 ≥ 3 时必须用对象映射表

- **Severity**: critical
- **Description**: 前端 SSE 事件处理器事件类型 ≥ `sse_event_dispatch.object_dispatch_threshold`（默认 3）时必须用 `Record<string, Handler>` 对象映射表替代 if/else 链，控制 SonarQube S3776 认知复杂度 < `sse_event_dispatch.cognitive_complexity_limit`（默认 15）。if/else 链认知复杂度随事件类型线性增长，6 个事件类型即超 15。评审时确认：前端事件处理器事件类型 ≥ 3 时用对象映射表。
- **Suggested fix**:

```typescript
// 错误：前端用 if/else if 链，认知复杂度高
if (eventName === 'text') { appendText(data); }
else if (eventName === 'image') { setImageUrl(data); }
else if (eventName === 'ppt') { setPptContent(data); }
else if (eventName === 'video') { setVideoUrl(data); }
else if (eventName === 'error') { setError(data); }
// ❌ SonarQube S3776 认知复杂度 > 15

// 正确：对象映射表，新增事件只需追加 handlers 一行
type SSEEventHandler = (data: any) => void;
const handlers: Record<string, SSEEventHandler> = {
  text: (data) => { appendText(data); },
  image: (data) => { setImageUrl(data); },
  ppt: (data) => { setPptContent(data); },
  video: (data) => { setVideoUrl(data); },
  error: (data) => { setError(data); }, // ✅
};
const handler = handlers[eventName];
if (handler) handler(data);
```

### BR-060-3：outputMode 必须用联合字面量类型，禁止 string 泛型

- **Severity**: critical
- **Description**: outputMode 必须用 TypeScript 联合字面量类型（`'normal' | 'mindmap' | 'image' | 'ppt' | 'video'`），禁止用 `string` 泛型。联合字面量类型提供编译期类型安全，新增模式追加字面量不破坏旧客户端；string 泛型无类型检查，拼写错误编译期不报错。评审时确认：outputMode 类型声明为联合字面量，非 string。
- **Suggested fix**:

```typescript
// 错误：outputMode 用 string 泛型，无类型安全
type OutputMode = string; // ❌ 拼写错误编译期不报错

// 正确：联合字面量类型
type OutputMode = 'normal' | 'mindmap' | 'image' | 'ppt' | 'video'; // ✅
```

### BR-060-4：outputMode 与 outputModes 必须正交分离，禁止混用

- **Severity**: suggestion
- **Description**: `outputMode`（结构模式，决定渲染组件）与 `outputModes`（事件可见性，决定哪些事件可见）正交分离，不可混用。混用会导致逻辑耦合（修改渲染模式影响事件可见性，反之亦然）。评审时确认：outputMode 与 outputModes 不在同一处判断，前者决定渲染组件，后者决定事件可见性。
- **Suggested fix**:

```typescript
// 错误：outputMode 与 outputModes 混用
function render(mode: string, visibleModes: string[]) {
  if (mode === 'image' && visibleModes.includes('image')) { // ❌ 正交概念不应同处判断
    renderImage();
  }
}

// 正确：正交分离
function renderByMode(mode: OutputMode) {
  if (mode === 'image') renderImageComponent(); // ✅ outputMode 决定渲染组件
}
function filterVisibleEvents(events: Event[], visibleModes: string[]) {
  return events.filter(e => visibleModes.includes(e.type)); // ✅ outputModes 决定事件可见性
}
```

### BR-060-5：未知事件必须有默认 handler，禁止静默吞掉

- **Severity**: critical
- **Description**: 对象映射表必须含 default handler，按 `sse_event_dispatch.unknown_event_strategy`（默认 `warn`）处理未知事件。未知事件静默吞掉会导致调试困难（新事件类型未注册时无任何提示）。评审时确认：对象映射表查找失败时有 `console.warn` / `throw` / 显式 return，非静默通过。
- **Suggested fix**:

```typescript
// 错误：未知事件静默吞掉
const handler = handlers[eventName];
if (handler) handler(data);
// ❌ 未知事件无任何处理，调试困难

// 正确：未知事件默认 handler 行为明确
const handler = handlers[eventName];
if (handler) {
  handler(data);
} else {
  console.warn(`[SSE] 未知事件类型: ${eventName}`); // ✅ warn 策略
}
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `sse_event_dispatch.enabled` | `true` | 是否启用本组规则（BR-060） |
| `sse_event_dispatch.severity_br060_1` | `critical` | BR-060-1 后端 if/else 链违规严重级别 |
| `sse_event_dispatch.severity_br060_2` | `critical` | BR-060-2 前端未用对象映射表违规严重级别 |
| `sse_event_dispatch.severity_br060_3` | `critical` | BR-060-3 outputMode 用 string 违规严重级别 |
| `sse_event_dispatch.severity_br060_4` | `suggestion` | BR-060-4 outputMode 与 outputModes 混用违规严重级别 |
| `sse_event_dispatch.severity_br060_5` | `critical` | BR-060-5 未知事件静默吞掉违规严重级别 |
| `sse_event_dispatch.object_dispatch_threshold` | `3` | 事件类型 ≥ 此值时必须用对象映射表 |
| `sse_event_dispatch.cognitive_complexity_limit` | `15` | SonarQube S3776 认知复杂度上限 |
| `sse_event_dispatch.unknown_event_strategy` | `warn` | 未知事件处理策略（warn / error / ignore） |
| `sse_event_dispatch.allowed_output_modes` | `normal,mindmap,image,ppt,video` | 允许的 outputMode 枚举 |

## 检查方式

1. **后端分发检查**：用 Grep 检索后端 SSE 路由（`text/event-stream` / `reply.raw.write`），确认事件分发用独立 if（无 `else if` / `else`）。用 if/else if/else 链 → **BR-060-1 违规**。
2. **前端映射表检查**：用 Grep 检索前端 SSE 事件处理器（`consumeSSE` / `handleEvent` 等），统计 if/else if 分支数。分支数 ≥ `object_dispatch_threshold`（3）且未用 `Record<string, Handler>` → **BR-060-2 违规**。
3. **类型检查**：用 Grep 检索 `type OutputMode` 声明，确认为联合字面量类型（含 `|` 分隔的字面量），非 `string`。用 string → **BR-060-3 违规**。
4. **正交分离检查**：用 Grep 检索同时含 `outputMode` 和 `outputModes` 的函数，确认两者不在同一 if 条件中。混用 → **BR-060-4 违规**（suggestion）。
5. **未知事件检查**：用 Grep 检索对象映射表查找代码（`handlers[eventName]`），确认查找失败时有 `console.warn` / `throw` / 显式 return。静默通过 → **BR-060-5 违规**。
6. **认知复杂度检查**：用 SonarQube 扫描前端 SSE 事件处理函数，确认 S3776 认知复杂度 < `cognitive_complexity_limit`（15）。超限 → **BR-060-2 违规**。

## 正确示例

```typescript
// services/api/src/routes/query.ts（后端 SSE 分发）
// ✅ 按字段独立 if 分发，新增事件类型只需追加 if 分支（BR-060-1）
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
// ✅ outputMode 联合字面量类型（BR-060-3）
type OutputMode = 'normal' | 'mindmap' | 'image' | 'ppt' | 'video';

// ✅ 事件处理器对象映射表，控制认知复杂度（BR-060-2）
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
      // ✅ 对象映射表分发（BR-060-2）
      const handler = handlers[eventName];
      if (handler) {
        handler(data);
      } else {
        // ✅ 未知事件默认 handler 行为明确（BR-060-5）
        console.warn(`[SSE] 未知事件类型: ${eventName}`);
      }
    }
  }
}

// ✅ outputMode 与 outputModes 正交分离（BR-060-4）
function renderByMode(mode: OutputMode) {
  if (mode === 'image') renderImageComponent(); // ✅ outputMode 决定渲染组件
}
function filterVisibleEvents(events: Event[], visibleModes: string[]) {
  return events.filter(e => visibleModes.includes(e.type)); // ✅ outputModes 决定事件可见性
}
```

## 错误示例

```typescript
// 错误 1：后端用 if/else if/else 链（BR-060-1 违规）
if (chunk.text) {
  raw.write(`event: text\ndata: ${JSON.stringify(chunk.text)}\n\n`);
} else if (chunk.image) {
  raw.write(`event: image\ndata: ${JSON.stringify(chunk.image)}\n\n`);
} else {
  raw.write(`event: unknown\ndata: ${JSON.stringify(chunk)}\n\n`); // ❌ 新增事件需修改此处
}

// 错误 2：前端用 if/else if 链，认知复杂度高（BR-060-2 违规）
if (eventName === 'text') { appendText(data); }
else if (eventName === 'image') { setImageUrl(data); }
else if (eventName === 'ppt') { setPptContent(data); }
else if (eventName === 'video') { setVideoUrl(data); }
else if (eventName === 'error') { setError(data); }
// ❌ SonarQube S3776 认知复杂度 > 15

// 错误 3：outputMode 用 string 泛型（BR-060-3 违规）
type OutputMode = string; // ❌ 无类型安全

// 错误 4：outputMode 与 outputModes 混用（BR-060-4 违规，suggestion）
function render(mode: string, visibleModes: string[]) {
  if (mode === 'image' && visibleModes.includes('image')) { // ❌ 正交概念不应同处判断
    renderImage();
  }
}

// 错误 5：未知事件静默吞掉（BR-060-5 违规）
const handler = handlers[eventName];
if (handler) handler(data);
// ❌ 未知事件无任何处理
```

## 适配新项目

- **WebSocket 项目**：将 SSE 事件改为 WebSocket 消息，对象映射表结构不变
- **EventSource polyfill 项目**：用 `EventSource` API，`addEventListener(eventName, handler)` 替代对象映射表
- **gRPC streaming 项目**：将 chunk 字段改为 proto message oneof，对象映射表按 oneof case 分发
- **React/Vue 项目**：对象映射表的 handler 改为 setState / ref 操作，配合框架响应式系统
- **非 TypeScript 项目**：outputMode 联合字面量类型改为字符串常量 `const OUTPUT_MODES = ['normal', 'mindmap', ...] as const`

## 与其他规则的关系

- 与 BR-027（SSE 事件类型扩展路由同步）联动：本规则关注事件分发模式（对象映射表 vs if/else），BR-027 关注事件类型登记与前端 handler 同步
- 与 BR-057（长/短任务架构分离）联动：秒级任务走 SSE 时用本规则的事件分发模式
- 与 BR-026（API 响应类型同步）联动：outputMode 联合字面量类型必须前后端同步
- 与 BR-ESM-03（静态分析建议人工验证）联动：SonarQube S3776 认知复杂度超限时，用对象映射表降低复杂度
- 与 CODING-063（SSE 事件对象映射分发）对应：本规则是 CODING-063 的后端审查视角
