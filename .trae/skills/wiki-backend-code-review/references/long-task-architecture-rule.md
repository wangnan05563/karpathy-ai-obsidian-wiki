# 长/短任务架构分离审查规则（BR-057）

> 复盘来源：v3 媒体生成工具开发中，视频生成需数分钟，超出 query SSE 流 60 秒超时，导致 SSE 流被中断。改用独立 JSON 端点（POST /api/media/video 创建任务 + GET /api/media/video/:taskId 前端轮询）。同时引入限流分级（破坏性端点 5/min，高频轮询 60/min）、错误码区分（配置缺失 400 vs API 失败 500）、双日志通道（前端响应 + 后端 request.log.error）、路由设计哲学顶部注释（CODING-059）。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"长/短任务架构分离审查参数（long_task_architecture）"章节读取，禁止在本规则文件硬编码限流值或超时阈值。

## Trigger Keywords

SSE, text/event-stream, rateLimit, timeWindow, destructive, poll, setInterval, request.log.error, reply.code, 400, 500, not configured, 设计要点, 路由注释, 长任务, 异步任务, video generation, batch processing

## Rules

### BR-057-1：分钟级任务必须走独立 JSON 端点 + 前端轮询，禁止走 SSE 流

- **Severity**: critical
- **Description**: 任务预估耗时 > `long_task_architecture.sse_threshold_ms`（默认 30000ms）时必须走独立 JSON 端点（POST 创建任务 + GET 轮询状态）+ 前端轮询，禁止走 SSE 流。SSE 流有 60 秒超时限制，视频生成需数分钟会超出 SSE 超时导致流被中断。评审时确认：长任务（视频生成/批量处理等）路由注册为独立 JSON 端点，而非复用 `/api/query` SSE 通道。
- **Suggested fix**:

```typescript
// 错误：长任务走 SSE 流，超时被中断
app.post('/api/query', async (request, reply) => {
  reply.raw.writeHead(200, { 'Content-Type': 'text/event-stream' });
  const result = await adapter.generateVideo(prompt); // ❌ 视频生成需 5 分钟，SSE 60s 超时
  reply.raw.write(`event: video\ndata: ${JSON.stringify(result)}\n\n`);
});

// 正确：长任务走独立 JSON 端点 + 前端轮询
app.post('/api/media/video', async (request, reply) => {
  const result = await adapter.generateVideo(prompt); // ✅ 异步创建任务
  return reply.send({ ok: true, taskId: result.taskId });
});
app.get('/api/media/video/:taskId', async (request, reply) => {
  const status = await adapter.getVideoTaskStatus(taskId); // ✅ 前端轮询
  return reply.send(status);
});
```

### BR-057-2：破坏性端点必须限流，禁止无限触发外部 API 成本

- **Severity**: critical
- **Description**: 破坏性端点（触发 LLM/外部 API 成本的端点，如 POST 创建任务）必须配置 `rateLimit`，限流 ≤ `long_task_architecture.destructive_rate_limit`（默认 5/min）。无限流会导致用户无限触发外部 API 成本。评审时确认：破坏性端点的路由配置含 `rateLimit: { max, timeWindow }`，且 max ≤ `destructive_rate_limit`。
- **Suggested fix**:

```typescript
// 错误：破坏性端点不限流，用户可无限触发外部 API 成本
app.post('/api/media/video', async (request, reply) => { // ❌ 缺少 rateLimit 配置
  const result = await adapter.generateVideo(prompt);
});

// 正确：5/min 限流（与 podcast 一致，触发外部 API 成本）
const lt = config.long_task_architecture;
app.post('/api/media/video', {
  config: { rateLimit: { max: lt.destructive_rate_limit, timeWindow: lt.destructive_rate_window } }, // ✅
}, async (request, reply) => {
  const result = await adapter.generateVideo(prompt);
});
```

### BR-057-3：错误码必须区分配置缺失（400）与 API 失败（500）

- **Severity**: critical
- **Description**: 错误处理必须用 `message.includes(long_task_architecture.config_error_keyword)`（默认 `not configured`）区分配置缺失（返 `config_error_status` 400）与外部 API 失败（返 `api_error_status` 500）。配置缺失是用户可修复的（去配置 apiKey），API 失败需重试或联系管理员。统一返 500 会让用户误以为服务故障，实际只需配置 apiKey。评审时确认：catch 块内有条件分支区分 400/500。
- **Suggested fix**:

```typescript
// 错误：所有错误统一返 500，用户无法区分配置缺失与 API 失败
catch (err) {
  return reply.code(500).send({ error: err.message }); // ❌ 配置缺失应返 400
}

// 正确：错误码区分配置缺失（400）与 API 失败（500）
const lt = config.long_task_architecture;
catch (err) {
  const message = err instanceof Error ? err.message : String(err);
  const isConfigError = message.includes(lt.config_error_keyword); // ✅ "not configured"
  return reply.code(isConfigError ? lt.config_error_status : lt.api_error_status)
    .send({ ok: false, error: message }); // ✅ 400 or 500
}
```

### BR-057-4：错误必须双日志通道（前端响应 + 后端 request.log.error）

- **Severity**: critical
- **Description**: 错误必须同时输出到两条通道——JSON 响应给前端用户看 + `request.log.error(...)` 写后端日志流供排障。只给前端响应不写后端日志，排障时无日志可查；只写后端日志不给前端响应，用户不知道发生了什么。评审时确认：catch 块内既有 `request.log.error(...)` 又有 `reply.code(...).send({ error })`。
- **Suggested fix**:

```typescript
// 错误：只给前端响应，不写后端日志，排障困难
catch (err) {
  return reply.code(500).send({ error: err.message }); // ❌ 缺少 request.log.error
}

// 正确：双日志通道
catch (err) {
  const message = err instanceof Error ? err.message : String(err);
  // ✅ 后端日志流供排障
  request.log.error({ err, prompt: body.prompt }, 'video generation create task failed');
  // ✅ JSON 响应给前端用户看
  return reply.code(500).send({ ok: false, error: message });
}
```

### BR-057-5：路由文件顶部必须有"设计要点"块注释

- **Severity**: suggestion
- **Description**: 每个路由文件顶部必须有"设计要点"块注释，列出端点职责、限流策略、关键设计决策的"为什么"。注释帮助后续维护者理解设计决策的背景（如"为什么视频走独立端点而非 SSE"），避免误改回 SSE 导致超时。评审时确认：路由文件顶部有含"设计要点"的块注释，且包含端点职责 + 限流策略 + 关键设计决策原因。
- **Suggested fix**:

```typescript
// 错误：路由文件无顶部注释，设计决策无文档
export function registerMediaRoute(app: FastifyInstance) { // ❌ 缺少"设计要点"块注释
  // ...
}

// 正确：顶部"设计要点"块注释
// services/api/src/routes/media.ts
// v3 媒体生成路由：视频生成异步任务
// 设计要点：
// 1. POST /api/media/video 创建任务（5/min 限流，与 podcast 一致，触发外部 API 成本）
// 2. GET /api/media/video/:taskId 轮询状态（60/min 限流，前端 5 秒间隔高频轮询）
// 3. 为什么视频走独立 JSON 端点而非 SSE：视频生成需数分钟，超出 query SSE 60 秒超时
// 4. 错误码：配置缺失返 400（用户可修复），API 失败返 500（用户需重试或联系管理员）
export function registerMediaRoute(app: FastifyInstance) { // ✅
  // ...
}
```

### BR-057-6：高频轮询端点限流必须与前端轮询间隔匹配

- **Severity**: suggestion
- **Description**: 高频轮询端点（GET 查询状态）限流 = `long_task_architecture.poll_rate_limit`（默认 60/min），必须与前端 `poll_interval_ms`（默认 5000ms = 12 次/min）匹配。限流过低会触发 429 导致前端轮询失败；限流过高浪费服务器资源。评审时确认：`poll_rate_limit` ≥ 60/min（前端 5s 间隔 = 12 次/min，60/min 有 5 倍余量）。
- **Suggested fix**:

```typescript
// 错误：轮询端点限流过低（10/min），前端 5s 间隔（12 次/min）会触发 429
app.get('/api/media/video/:taskId', {
  config: { rateLimit: { max: 10, timeWindow: '1 minute' } }, // ❌ 12 次/min > 10/min
}, async (request, reply) => { ... });

// 正确：60/min 限流（前端 5s 间隔 = 12 次/min，60/min 有 5 倍余量）
const lt = config.long_task_architecture;
app.get('/api/media/video/:taskId', {
  config: { rateLimit: { max: lt.poll_rate_limit, timeWindow: lt.poll_rate_window } }, // ✅ 60/min
}, async (request, reply) => { ... });
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `long_task_architecture.enabled` | `true` | 是否启用本组规则（BR-057） |
| `long_task_architecture.severity_br057_1` | `critical` | BR-057-1 长任务走 SSE 违规严重级别 |
| `long_task_architecture.severity_br057_2` | `critical` | BR-057-2 破坏性端点无限流违规严重级别 |
| `long_task_architecture.severity_br057_3` | `critical` | BR-057-3 错误码未区分违规严重级别 |
| `long_task_architecture.severity_br057_4` | `critical` | BR-057-4 单日志通道违规严重级别 |
| `long_task_architecture.severity_br057_5` | `suggestion` | BR-057-5 缺少顶部注释违规严重级别 |
| `long_task_architecture.severity_br057_6` | `suggestion` | BR-057-6 限流不匹配违规严重级别 |
| `long_task_architecture.sse_threshold_ms` | `30000` | SSE 流超时阈值（毫秒），超过此值走独立端点 |
| `long_task_architecture.destructive_rate_limit` | `5` | 破坏性端点限流（次/分钟） |
| `long_task_architecture.destructive_rate_window` | `1 minute` | 破坏性端点限流窗口 |
| `long_task_architecture.poll_rate_limit` | `60` | 高频轮询端点限流（次/分钟） |
| `long_task_architecture.poll_rate_window` | `1 minute` | 高频轮询端点限流窗口 |
| `long_task_architecture.poll_interval_ms` | `5000` | 前端轮询间隔（毫秒） |
| `long_task_architecture.config_error_keyword` | `not configured` | 配置缺失错误判定关键词 |
| `long_task_architecture.config_error_status` | `400` | 配置缺失错误 HTTP 状态码 |
| `long_task_architecture.api_error_status` | `500` | 外部 API 失败 HTTP 状态码 |

## 检查方式

1. **架构选择检查**：用 Grep 检索路由文件中的长任务关键词（`generateVideo` / `batchProcess` / `transcode` 等），确认对应路由注册为独立 JSON 端点（`app.post('/api/...'`）而非复用 `/api/query` SSE 通道。长任务走 SSE → **BR-057-1 违规**。
2. **限流分级检查**：用 Grep 检索破坏性端点（POST 创建任务）的路由配置，确认含 `rateLimit: { max, timeWindow }`。缺少 rateLimit → **BR-057-2 违规**。max > `destructive_rate_limit` → **BR-057-2 违规**。
3. **错误码区分检查**：用 Grep 检索 catch 块内的 `reply.code(` 调用，确认有条件分支（`isConfigError ? 400 : 500`）。统一返 500 → **BR-057-3 违规**。
4. **双日志通道检查**：用 Grep 检索 catch 块，确认既有 `request.log.error(...)` 又有 `reply.code(...).send({ error })`。缺少任一 → **BR-057-4 违规**。
5. **顶部注释检查**：用 Read 查看路由文件顶部 10 行，确认有"设计要点"块注释含端点职责 + 限流策略 + 设计决策原因。缺少 → **BR-057-5 违规**（suggestion）。
6. **限流匹配检查**：对比 `poll_rate_limit` 与 `poll_interval_ms`，确认 `poll_rate_limit` ≥ 60/min（前端 5s 间隔 = 12 次/min，需 5 倍余量）。不匹配 → **BR-057-6 违规**（suggestion）。

## 正确示例

```typescript
// services/api/src/routes/media.ts
// v3 媒体生成路由：视频生成异步任务
// 设计要点：
// 1. POST /api/media/video 创建任务（5/min 限流，与 podcast 一致，触发外部 API 成本）
// 2. GET /api/media/video/:taskId 轮询状态（60/min 限流，前端 5 秒间隔高频轮询）
// 3. 为什么视频走独立 JSON 端点而非 SSE：视频生成需数分钟，超出 query SSE 60 秒超时
// 4. 错误码：配置缺失返 400（用户可修复），API 失败返 500（用户需重试或联系管理员）

import type { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { config } from '../config.js';

const lt = config.long_task_architecture;

export function registerMediaRoute(app: FastifyInstance, adapter: HarnessAdapter) {
  // ✅ 破坏性端点：5/min 限流（BR-057-2）
  app.post('/api/media/video', {
    config: { rateLimit: { max: lt.destructive_rate_limit, timeWindow: lt.destructive_rate_window } },
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const body = request.body as { prompt: string };
      const result = await adapter.generateVideo(body.prompt);
      return reply.send({ ok: true, ...result });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);

      // ✅ 双日志通道：后端日志流供排障（BR-057-4）
      request.log.error({ err, prompt: body.prompt }, 'video generation create task failed');

      // ✅ 错误码区分：配置缺失返 400，API 失败返 500（BR-057-3）
      const isConfigError = message.includes(lt.config_error_keyword);
      return reply.code(isConfigError ? lt.config_error_status : lt.api_error_status)
        .send({ ok: false, error: message });
    }
  });

  // ✅ 高频轮询端点：60/min 限流（BR-057-6）
  app.get('/api/media/video/:taskId', {
    config: { rateLimit: { max: lt.poll_rate_limit, timeWindow: lt.poll_rate_window } },
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    const { taskId } = request.params as { taskId: string };
    const status = await adapter.getVideoTaskStatus(taskId);
    return reply.send(status);
  });
}
```

## 错误示例

```typescript
// 错误 1：长任务走 SSE 流，超时被中断（BR-057-1 违规）
app.post('/api/query', async (request, reply) => {
  reply.raw.writeHead(200, { 'Content-Type': 'text/event-stream' });
  const result = await adapter.generateVideo(prompt); // ❌ 视频生成需 5 分钟，SSE 60s 超时
  reply.raw.write(`event: video\ndata: ${JSON.stringify(result)}\n\n`);
});

// 错误 2：破坏性端点不限流（BR-057-2 违规）
app.post('/api/media/video', async (request, reply) => { // ❌ 缺少 rateLimit 配置
  const result = await adapter.generateVideo(prompt);
});

// 错误 3：所有错误统一返 500（BR-057-3 违规）
catch (err) {
  return reply.code(500).send({ error: err.message }); // ❌ 配置缺失应返 400
}

// 错误 4：只给前端响应，不写后端日志（BR-057-4 违规）
catch (err) {
  return reply.code(500).send({ error: err.message }); // ❌ 缺少 request.log.error
}

// 错误 5：路由文件无顶部注释（BR-057-5 违规，suggestion）
export function registerMediaRoute(app: FastifyInstance) { // ❌ 缺少"设计要点"块注释
  // ...
}

// 错误 6：轮询端点限流过低（BR-057-6 违规，suggestion）
app.get('/api/media/video/:taskId', {
  config: { rateLimit: { max: 10, timeWindow: '1 minute' } }, // ❌ 前端 5s 间隔 = 12 次/min > 10/min
}, ...);
```

## 适配新项目

- **任务队列项目（BullMQ / Celery）**：长任务改为入队 + 工作进程消费，前端轮询任务状态
- **WebSocket 项目**：长任务改为 WebSocket 推送进度，避免轮询开销
- **SSE 长连接项目**：SSE 超时改为 30 分钟（需 nginx / proxy 配合），仍可走 SSE
- **gRPC streaming 项目**：长任务改为 server streaming RPC，客户端实时接收进度
- **Python FastAPI 项目**：`rateLimit` 改为 `slowapi` 中间件，`request.log.error` 改为 `logging.error`

## 与其他规则的关系

- 与 BR-054（外部 API 集成契约）联动：长任务端点的外部 API 调用必须用 fetchWithDiagnostics 包装
- 与 BR-055（超时分级策略）联动：长任务的创建/轮询/下载三阶段分别用不同超时分级
- 与 BR-058（媒体归档 frontmatter）联动：长任务产物归档到 vault queries/ 目录
- 与 BR-027（SSE 事件类型扩展路由同步）联动：秒级任务走 SSE 时用 BR-027 的事件类型同步
- 与 BR-034（配置化参数检测）联动：限流值必须从 config 读取，禁止硬编码
- 与 CODING-059（长/短任务架构分离）对应：本规则是 CODING-059 的后端审查视角
