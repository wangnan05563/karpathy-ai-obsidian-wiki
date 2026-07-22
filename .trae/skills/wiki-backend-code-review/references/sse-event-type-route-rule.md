# SSE 事件类型扩展路由同步（BR-027）

> 复盘来源：后端新增 SSE 事件类型（如 `warning` / `metadata` / `tool_call`）后未同步更新 config 事件类型列表与前端 `consumeSSEStream` 处理逻辑，导致前端默认 handler 静默吞掉未知事件、用户看不到关键提示、调试时难以追踪事件丢失。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"sse_event_type_route"章节读取，禁止在本规则文件硬编码具体事件类型名或文件路径。

## Trigger Keywords
text/event-stream, reply.raw.write, reply.raw.writeHead, event: xxx, SSE event types, consumeSSEStream, EventSource, event_type, sse_event_types, writeSSE, sendSSE

## Rules

### BR-027-1: 新增 SSE 事件类型必须在 config 的 sse_event_types 列表中同步添加

- **Severity**: critical
- **Description**: 后端 SSE 路由中通过 `reply.raw.write('event: <type>\n')` 写入的事件类型必须登记在 config 的 `sse_event_types_config_field` 字段对应列表中。该列表是事件类型的契约下限——前端按列表生成 handler、文档按列表描述事件语义、测试按列表覆盖事件分支。新增事件类型未登记会导致：前端缺少对应 handler、文档遗漏、测试覆盖盲区。
- **Suggested fix**:
```typescript
// 1. 在 config/review-config.md 的 sse_event_type_route.sse_event_types 中追加新事件
//    sse_event_types: progress, result, error, done, warning, metadata

// 2. 后端发送事件时使用统一 helper（事件类型从 config 读取）
import { SSE_EVENT_TYPES } from '../config/sse-events.js';

app.get('/api/runs/:id/stream', async (request, reply) => {
  reply.raw.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
  });
  // 统一 helper：事件类型从 config 列表读取，禁止字面量硬编码
  await sendSSE(reply, SSE_EVENT_TYPES.WARNING, { message: '预算即将耗尽' });
  return reply;
});
```

### BR-027-2: 新增 SSE 事件类型必须在前端 consumeSSEStream 中处理

- **Severity**: critical
- **Description**: 后端新增的 SSE 事件类型必须在前端 `consumeSSEStream`（或等价的事件消费函数）中添加对应 handler 分支。未知事件类型的默认 handler 行为必须明确（如 `console.warn` + 上报监控），禁止静默吞掉——否则用户无法感知后端推送的关键提示（如 `warning` 事件），调试时也难以发现事件被丢弃。
- **Suggested fix**:
```typescript
// frontend/src/lib/sse.ts —— 同步新增 handler
type SSEEventHandler = (data: unknown) => void;

interface SSEHandlers {
  progress?: SSEEventHandler;
  result?: SSEEventHandler;
  error?: SSEEventHandler;
  done?: SSEEventHandler;
  warning?: SSEEventHandler;   // 后端新增 → 前端同步新增
  metadata?: SSEEventHandler;  // 后端新增 → 前端同步新增
}

export async function consumeSSEStream(
  url: string,
  handlers: SSEHandlers,
): Promise<void> {
  const response = await fetch(url);
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const events = buffer.split('\n\n');
    buffer = events.pop() ?? '';

    for (const evt of events) {
      const eventType = /event: (.+)/.exec(evt)?.[1]?.trim();
      const data = /data: (.+)/.exec(evt)?.[1];
      if (!eventType) continue;

      const handler = handlers[eventType as keyof SSEHandlers];
      if (handler) {
        handler(data ? JSON.parse(data) : null);
      } else {
        // 未知事件类型：明确告警，禁止静默吞掉
        console.warn(`[SSE] 未处理的事件类型: ${eventType}`);
      }
    }
  }
}
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `sse_event_type_route.enabled` | `true` | 是否启用本规则 |
| `sse_event_type_route.severity` | `critical` | 违规严重级别 |
| `sse_event_type_route.sse_event_types_config_field` | `sse.event_types` | config 中事件类型列表的字段名 |
| `sse_event_type_route.required_event_types` | `progress,result,error,done` | 必备事件类型（契约下限，逗号分隔） |
| `sse_event_type_route.backend_sse_routes_directory` | `api/src/routes/` | 后端 SSE 路由所在目录 |
| `sse_event_type_route.event_pattern` | `event:\s*\w+` | SSE 事件类型字面量匹配模式（正则） |
| `sse_event_type_route.frontend_sse_consumer_path` | `frontend/src/lib/sse.ts` | 前端 SSE 消费函数文件路径 |
| `sse_event_type_route.unknown_event_strategy` | `warn` | 未知事件类型的默认处理策略（`warn` / `error` / `ignore`） |

## 检查方式

1. 用 Grep 检索 `sse_event_type_route.backend_sse_routes_directory` 下所有 `.ts` 文件，匹配 `sse_event_type_route.event_pattern`（如 `event:\s*\w+`）。
2. 提取所有唯一的事件类型字面量集合 `B`。
3. 用 Read 读取 config，从 `sse_event_type_route.sse_event_types_config_field` 字段提取已登记事件类型集合 `C`。
4. 对比 `B` 与 `C`：
   - `B - C` 非空 → BR-027-1 违规（后端发送了未登记的事件类型）
   - `sse_event_type_route.required_event_types` 中任一类型不在 `C` 中 → 违规（必备事件缺失）
5. 用 Read 读取 `sse_event_type_route.frontend_sse_consumer_path`，提取 handler 分支覆盖的事件类型集合 `F`。
6. 对比 `B` 与 `F`：
   - `B - F` 非空 → BR-027-2 违规（前端缺少对应 handler）
7. 检查默认 handler 分支：若 `unknown_event_strategy` 为 `warn`，确认未知事件触发 `console.warn` 而非静默 return。

## 正确示例

```typescript
// 1. config/review-config.md —— 事件类型契约
// sse_event_type_route.sse_event_types: progress,result,error,done,warning,metadata

// 2. api/src/routes/runs.ts —— 后端发送
import { sendSSE, SSE_EVENT_TYPES } from '../utils/sse.js';

app.get('/api/runs/:id/stream', async (request, reply) => {
  reply.raw.writeHead(200, { 'Content-Type': 'text/event-stream' });
  try {
    for await (const evt of runEngine(request.params.id)) {
      if (evt.type === 'warning') {
        await sendSSE(reply, SSE_EVENT_TYPES.WARNING, evt);  // 类型从 config 读取
      } else {
        await sendSSE(reply, evt.type, evt);
      }
    }
    await sendSSE(reply, SSE_EVENT_TYPES.DONE, {});
  } finally {
    reply.raw.end();
  }
  return reply;
});

// 3. frontend/src/lib/sse.ts —— 前端同步 handler
consumeSSEStream(`/api/runs/${id}/stream`, {
  progress: (d) => setProgress(d.percent),
  result: (d) => appendResult(d),
  error: (d) => showError(d.message),
  done: () => setStatus('done'),
  warning: (d) => showWarning(d.message),  // 后端新增 → 前端同步
  metadata: (d) => setMetadata(d),         // 后端新增 → 前端同步
});
```

## 错误示例

```typescript
// 错误 1：后端新增事件类型，config 未登记
// api/src/routes/runs.ts
reply.raw.write('event: warning\n');       // 后端发送 warning 事件
reply.raw.write(`data: ${JSON.stringify({ message: '预算低' })}\n\n`);

// config 中 sse_event_type_route.sse_event_types 仅含 progress,result,error,done
// ❌ warning 未登记，前端 handler 不会生成

// 错误 2：前端默认 handler 静默吞掉未知事件
// frontend/src/lib/sse.ts
const handler = handlers[eventType];
if (handler) {
  handler(data);
}
// ❌ 缺 else 分支，未知事件被静默丢弃，用户无法感知 warning 提示

// 错误 3：事件类型字面量硬编码，未从 config 读取
// api/src/routes/runs.ts
reply.raw.write('event: warning\n');  // ❌ 字面量硬编码，与 config 列表脱钩
// 应改为：reply.raw.write(`event: ${SSE_EVENT_TYPES.WARNING}\n`);
```

## 适配新项目

- **Express 项目**：将 `reply.raw.write` 替换为 `res.write`，`reply.raw.writeHead` 替换为 `res.writeHead`，`event_pattern` 不变；helper 函数签名调整为 `sendSSE(res, type, data)`。
- **NestJS 项目**：SSE 通过 `@Sse()` 装饰器 + RxJS `Observable` 实现，事件类型在 `mapTo({ type: 'warning', data })` 中字面量定义——将 `backend_sse_routes_directory` 改为 `src/controllers/`，`event_pattern` 调整为 `type:\s*['"]\w+['"]`，其余规则不变。
- **Koa 项目**：将 `reply.raw.write` 替换为 `ctx.res.write`，其余规则不变。
- **GraphQL Subscription 项目**：事件类型由 GraphQL schema 的 `type Subscription` 定义，本规则不适用，可在 `enabled` 设为 `false`，改由 schema-first 类型同步规则覆盖。
- **WebSocket 项目**：事件类型通过消息体的 `type` 字段约定，将 `event_pattern` 调整为 `type:\s*['"]\w+['"]`，`frontend_sse_consumer_path` 改为 WebSocket 消息处理函数路径。
