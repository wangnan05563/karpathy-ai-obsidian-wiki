# 长/短任务架构分离规则（CODING-059）

> 复盘来源：v3 媒体生成工具开发中，视频生成需数分钟，超出 query SSE 流 60 秒超时，导致 SSE 流被中断。改用独立 JSON 端点（POST /api/media/video 创建任务 + GET /api/media/video/:taskId 前端轮询）。同时引入限流分级（破坏性端点 5/min，高频轮询 60/min）、错误码区分（配置缺失 400 vs API 失败 500）、双日志通道（前端响应 + 后端 request.log.error）、路由设计哲学顶部注释。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `long_task` 字段读取，禁止在规则文件中硬编码限流值或超时阈值。

## 规则

**新增功能涉及异步任务时必须按任务耗时选择架构**：

1. **秒级任务（≤ `long_task.sse_threshold_ms`，默认 30000ms）**：走 SSE 同步流，复用 query 通道，前端实时接收事件
2. **分钟级任务（> `long_task.sse_threshold_ms`）**：走独立 JSON 端点 + 前端轮询，避免 SSE 超时
3. **破坏性端点限流**：触发 LLM/外部 API 成本的端点限流 ≤ `long_task.destructive_rate_limit`（默认 5/min）
4. **高频轮询端点限流**：轮询端点限流 = `long_task.poll_rate_limit`（默认 60/min，与前端 `poll_interval_ms` 匹配）
5. **错误码区分**：配置缺失返 400，外部 API 失败返 500（用 `message.includes('not configured')` 判定）
6. **双日志通道**：错误必须同时输出到两条通道——JSON 响应给前端用户看 + `request.log.error` 写后端日志流供排障
7. **路由设计哲学顶部注释**：每个路由文件顶部必须有"设计要点"块注释，列出端点职责、限流策略、关键设计决策的"为什么"

## 适用场景

- 异步任务功能（视频生成、批量处理、长时 LLM 调用、文件转码等）
- 需要限流的破坏性端点（触发外部 API 成本、不可逆操作）
- 前端轮询场景（创建任务 + 轮询状态 + 获取结果三阶段）
- 需要前后端协同的长时操作（前端显示进度，后端异步执行）

## 不适用场景

- 秒级同步请求（直接用 SSE 流或单次 JSON 请求即可）
- 内部后台任务（无需前端轮询，用任务队列 + 通知机制）
- 一次性脚本（无需限流，无需前后端协同）
- 无成本的操作（如本地文件读取，无需破坏性端点限流）

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `long_task.sse_threshold_ms` | `30000` | SSE 流超时阈值（毫秒），超过此值的任务走独立端点 |
| `long_task.destructive_rate_limit` | `5` | 破坏性端点限流（次/分钟） |
| `long_task.destructive_rate_window` | `1 minute` | 破坏性端点限流窗口 |
| `long_task.poll_rate_limit` | `60` | 高频轮询端点限流（次/分钟） |
| `long_task.poll_rate_window` | `1 minute` | 高频轮询端点限流窗口 |
| `long_task.poll_interval_ms` | `5000` | 前端轮询间隔（毫秒） |
| `long_task.config_error_keyword` | `not configured` | 配置缺失错误判定关键词 |
| `long_task.config_error_status` | `400` | 配置缺失错误 HTTP 状态码 |
| `long_task.api_error_status` | `500` | 外部 API 失败 HTTP 状态码 |

## 检查方式

1. **架构选择检查**：任务预估耗时 > `sse_threshold_ms` 时必须走独立端点 + 轮询，禁止走 SSE 流
2. **限流分级检查**：破坏性端点（POST 创建任务）限流 ≤ `destructive_rate_limit`，轮询端点（GET 查询状态）限流 = `poll_rate_limit`
3. **错误码区分检查**：错误处理必须用 `message.includes(config_error_keyword)` 区分配置错误（400）与 API 失败（500）
4. **双日志通道检查**：错误处理必须同时 `request.log.error(...)` 写后端日志 + `reply.code(...).send({ error })` 给前端
5. **顶部注释检查**：路由文件顶部必须有"设计要点"块注释，含端点职责、限流策略、关键设计决策的"为什么"
6. **前端轮询间隔检查**：前端 `setInterval` 间隔必须 = `poll_interval_ms`，与后端限流值匹配（避免触发 429）

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

const lt = config.long_task;

export function registerMediaRoute(app: FastifyInstance, adapter: HarnessAdapter) {
  // ✅ 破坏性端点：5/min 限流（与 podcast 一致，触发外部 API 成本）
  app.post('/api/media/video', {
    config: { rateLimit: { max: lt.destructive_rate_limit, timeWindow: lt.destructive_rate_window } },
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    try {
      const body = request.body as { prompt: string };
      const result = await adapter.generateVideo(body.prompt);
      return reply.send({ ok: true, ...result });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);

      // ✅ 双日志通道：后端日志流供排障
      request.log.error({ err, prompt: body.prompt }, 'video generation create task failed');

      // ✅ 错误码区分：配置缺失返 400，API 失败返 500
      const isConfigError = message.includes(lt.config_error_keyword);
      return reply.code(isConfigError ? lt.config_error_status : lt.api_error_status)
        .send({ ok: false, error: message });
    }
  });

  // ✅ 高频轮询端点：60/min 限流（与前端 5s 间隔匹配，10 次/分钟）
  app.get('/api/media/video/:taskId', {
    config: { rateLimit: { max: lt.poll_rate_limit, timeWindow: lt.poll_rate_window } },
  }, async (request: FastifyRequest, reply: FastifyReply) => {
    // ...轮询逻辑
  });
}
```

## 错误示例

```typescript
// ❌ 错误：长任务走 SSE 流，超时被中断
app.post('/api/query', async (request, reply) => {
  reply.raw.writeHead(200, { 'Content-Type': 'text/event-stream' });
  const result = await adapter.generateVideo(prompt); // ❌ 视频生成需 5 分钟，SSE 60s 超时
  reply.raw.write(`event: video\ndata: ${JSON.stringify(result)}\n\n`);
});

// ❌ 错误：破坏性端点不限流，用户可无限触发外部 API 成本
app.post('/api/media/video', async (request, reply) => { // ❌ 缺少 rateLimit 配置
  const result = await adapter.generateVideo(prompt);
});

// ❌ 错误：所有错误统一返 500，用户无法区分配置缺失与 API 失败
catch (err) {
  return reply.code(500).send({ error: err.message }); // ❌ 配置缺失应返 400
}

// ❌ 错误：只给前端响应，不写后端日志，排障困难
catch (err) {
  return reply.code(500).send({ error: err.message }); // ❌ 缺少 request.log.error
}

// ❌ 错误：路由文件无顶部注释，设计决策无文档
export function registerMediaRoute(app: FastifyInstance) { // ❌ 缺少"设计要点"块注释
  // ...
}
```

## 适配新项目

- 适配任务队列（BullMQ / Celery）：长任务改为入队 + 工作进程消费，前端轮询任务状态
- 适配 WebSocket：长任务改为 WebSocket 推送进度，避免轮询开销
- 适配 Server-Sent Events 长连接：SSE 超时改为 30 分钟（需 nginx / proxy 配合），仍可走 SSE
- 适配 gRPC streaming：长任务改为 server streaming RPC，客户端实时接收进度

## 与其他规则的关系

- 与 CODING-056（外部 API 集成契约）联动：长任务端点的外部 API 调用必须用 fetchWithDiagnostics 包装
- 与 CODING-057（超时分级策略）联动：长任务的创建/轮询/下载三阶段分别用不同超时分级
- 与 CODING-060（媒体归档 frontmatter 标准化）联动：长任务产物归档到 vault queries/ 目录
- 与 CODING-065（长任务轮询 UI 模式）联动：前端轮询 UI 必须按 5 状态机驱动
- 与 CODING-013（优雅停止）联动：长任务进行中服务退出时，必须通知前端并清理任务状态
