# SSE 流式输出规范

本文档记录 Karpathy Wiki 项目中 SSE（Server-Sent Events）的实现标准。

## 基本格式

```
event: <event_type>
data: <JSON_string>
\n
```

每个事件以双换行符 `\n\n` 结尾。

## Headers 设置

SSE 路由必须设置完整的 headers：

```typescript
reply.raw.writeHead(200, {
  'Content-Type': 'text/event-stream',
  'Cache-Control': 'no-cache',
  Connection: 'keep-alive',
  'X-Accel-Buffering': 'no'  // 禁用 nginx 缓冲
});
```

## 事件类型

根据 `config/tech-stack.json` 中定义的 `sseEventTypes`：

| 功能 | 事件类型 | 说明 |
|---|---|---|
| compile | progress/page/done/error | 编译过程 |
| query | answer/refs/done/error | 知识查询 |
| healthCheck | scan/finding/done/error | 健康检查 |
| healthCheckFix | fixing/fixed/done/error | 健康修复 |

## 实现模板

```typescript
app.get('/api/wiki/<action>', async (request, reply) => {
  const { param } = request.query;

  // 1. 设置 SSE headers
  reply.raw.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    Connection: 'keep-alive',
    'X-Accel-Buffering': 'no'
  });

  let stream: AsyncIterable<InternalEvent> | null = null;

  try {
    // 2. 创建事件流
    stream = createWorkflow(param);

    // 3. 消费并转发
    for await (const event of stream) {
      const sseLine = `event: ${event.type}\ndata: ${JSON.stringify(event.data)}\n\n`;
      reply.raw.write(sseLine);
    }

    // 4. 发送完成事件
    reply.raw.write('event: done\ndata: {"status":"complete"}\n\n');
  } catch (err) {
    // 5. 错误通过 error 事件推送
    const msg = err instanceof Error ? err.message : 'Unknown error';
    reply.raw.write(`event: error\ndata: {"status":"error","message":"${msg}"}\n\n`);
  } finally {
    // 6. 必须关闭连接
    reply.raw.end();
  }
});
```

## 禁止事项

| 禁止项 | 原因 |
|---|---|
| `return reply.send()` | 关闭流，客户端收不到增量数据 |
| 省略 `Cache-Control: no-cache` | 浏览器可能缓存 SSE 响应 |
| 省略 `X-Accel-Buffering: no` | nginx 可能缓冲整个响应 |
| 不在 finally 中调用 `reply.raw.end()` | 连接泄漏 |
| 直接 throw 错误 | SSE 客户端收到不完整响应 |

## send 辅助函数

建议统一封装 send 辅助函数：

```typescript
function sendSSE(reply: FastifyReply, type: string, data: unknown): void {
  const json = JSON.stringify(data);
  reply.raw.write(`event: ${type}\ndata: ${json}\n\n`);
}

// 使用
sendSSE(reply, 'progress', { page: 1, total: 10 });
sendSSE(reply, 'done', { status: 'complete' });
sendSSE(reply, 'error', { message: 'Something went wrong' });
```
