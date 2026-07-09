# Rule Catalog — SSE 流式输出

## Scope
- Covers: Fastify 路由中以 `text/event-stream` 形式返回的事件流实现，包括 headers 设置、事件写入、连接生命周期管理、错误推送方式。
- 适用对象：长任务路由（如编译、查询、批量生成）、`reply.raw.write` 相关代码、SSE 辅助函数。

## Rules

### SSE headers 必须完整且包含 X-Accel-Buffering
- Category: correctness
- Severity: critical
- Description: SSE 响应必须设置完整的 headers，否则会被 Nginx/代理缓冲导致事件无法实时推送到客户端。除了标准的 `Content-Type` / `Cache-Control` / `Connection` 外，必须显式设置 `X-Accel-Buffering: no` 以绕过 Nginx 的响应缓冲机制。
- Suggested fix: 在写入首个事件前一次性设置全部 headers，顺序固定，避免遗漏。
- Example:
  - Bad:
    ```typescript
    app.get('/stream', async (request, reply) => {
      // 仅设置 Content-Type，缺 Cache-Control / Connection / X-Accel-Buffering
      reply.raw.writeHead(200, { 'Content-Type': 'text/event-stream' });
      reply.raw.write(`data: ${JSON.stringify({ ok: true })}\n\n`);
    });
    ```
  - Good:
    ```typescript
    app.get('/stream', async (request, reply) => {
      reply.raw.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        // Nginx 默认会缓冲上游响应，必须显式关闭才能让事件实时透传到客户端
        'X-Accel-Buffering': 'no',
      });
      reply.raw.write(`data: ${JSON.stringify({ ok: true })}\n\n`);
    });
    ```

### 事件格式必须为 event + data 双行以 \n\n 结尾
- Category: correctness
- Severity: critical
- Description: SSE 协议要求事件以空行（`\n\n`）分隔；每个事件应包含 `event:` 行标识类型，`data:` 行承载 JSON 序列化后的单行字符串。多行 JSON 或缺失 `event:` 字段会导致客户端无法正确分发事件。
- Suggested fix: 封装统一的 `send` 辅助函数，强制 `event` 和 `data` 成对出现，并由 helper 负责拼接分隔符。
- Example:
  - Bad:
    ```typescript
    // 缺 event 行，且 JSON 被多行美化后写入，客户端解析会错乱
    reply.raw.write(JSON.stringify({ type: 'progress', pct: 50 }, null, 2));
    reply.raw.write('\n');
    ```
  - Good:
    ```typescript
    function send(raw: NodeJS.WritableStream, event: string, data: unknown): void {
      const payload = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
      raw.write(payload);
    }
    send(reply.raw, 'progress', { pct: 50 });
    ```

### 必须在 finally 中关闭 reply.raw.end()
- Category: reliability
- Severity: critical
- Description: SSE 连接是长连接，若不在 finally 中调用 `reply.raw.end()`，异常路径或正常结束都会导致连接泄漏、客户端永远等待。仅靠 `done` 事件不足以关闭传输层连接。
- Suggested fix: 用 `try/finally` 包裹整个流式写入逻辑，finally 中无条件调用 `reply.raw.end()`。
- Example:
  - Bad:
    ```typescript
    app.get('/stream', async (request, reply) => {
      for await (const ev of adapter.run()) {
        send(reply.raw, ev.type, ev.data);
      }
      // 缺 finally，一旦 adapter.run() 抛异常，连接永不关闭
    });
    ```
  - Good:
    ```typescript
    app.get('/stream', async (request, reply) => {
      try {
        for await (const ev of adapter.run()) {
          send(reply.raw, ev.type, ev.data);
        }
      } finally {
        // 无论正常结束还是异常，都必须关闭底层连接，避免连接泄漏
        reply.raw.end();
      }
    });
    ```

### 错误必须通过 error 事件推送而非抛异常断连
- Category: reliability
- Severity: critical
- Description: SSE 流中一旦抛出未捕获异常，连接会被 Fastify 以非 SSE 格式（如 JSON 错误）回写，客户端解析必然失败，且丢失已产出的事件上下文。错误应以 `error` 事件的形式推送给客户端，让客户端决定是否重试。
- Suggested fix: 在 try 块内捕获异常，先 `send(reply.raw, 'error', { message })`，再在 finally 中关闭连接。
- Example:
  - Bad:
    ```typescript
    try {
      for await (const ev of adapter.run()) {
        send(reply.raw, ev.type, ev.data);
      }
    } catch (err) {
      // 直接抛出会被 Fastify 包装成 JSON 错误响应，破坏 SSE 协议
      throw err;
    }
    ```
  - Good:
    ```typescript
    try {
      for await (const ev of adapter.run()) {
        send(reply.raw, ev.type, ev.data);
      }
    } catch (err) {
      // 通过 error 事件把错误信息推给客户端，保持 SSE 协议完整
      const message = err instanceof Error ? err.message : String(err);
      send(reply.raw, 'error', { message });
    } finally {
      reply.raw.end();
    }
    ```

### SSE 路由禁止使用 return reply.send()
- Category: correctness
- Severity: critical
- Description: SSE 路由已经通过 `reply.raw.writeHead` 接管了底层响应流。若再调用 `reply.send()` 或 `return reply.send()`，Fastify 会尝试再次写入响应体，导致 `ERR_STREAM_ALREADY_FINISHED` 或响应体被覆盖，客户端收不到任何 SSE 事件。
- Suggested fix: SSE 路由的 handler 不返回任何值（返回 `void` 或 `Promise<void>`），所有输出都通过 `reply.raw.write` 完成。
- Example:
  - Bad:
    ```typescript
    app.get('/stream', async (request, reply) => {
      reply.raw.writeHead(200, sseHeaders);
      reply.raw.write(`data: ...\n\n`);
      // 与 raw.writeHead 冲突，Fastify 会再次序列化并发送，破坏流
      return reply.send({ ok: true });
    });
    ```
  - Good:
    ```typescript
    app.get('/stream', async (request, reply) => {
      reply.raw.writeHead(200, sseHeaders);
      try {
        for await (const ev of adapter.run()) {
          send(reply.raw, ev.type, ev.data);
        }
      } finally {
        reply.raw.end();
      }
      // 不 return reply.send()，handler 显式返回 void
    });
    ```

### 事件写入应统一封装为 send 辅助函数
- Category: maintainability
- Severity: suggestion
- Description: 多处直接拼接 `event: ... \ndata: ... \n\n` 字符串会导致格式不一致（如漏写分隔符、JSON 未序列化）。统一封装 `send(raw, event, data)` 能集中维护事件格式契约，降低出错概率。
- Suggested fix: 在 routes 同级或 utils 下提供单一 `send` 函数，所有 SSE 路由复用，禁止散落的字符串拼接。
- Example:
  - Bad:
    ```typescript
    // 路由 A
    reply.raw.write(`event: progress\ndata: ${JSON.stringify({ pct: 10 })}\n\n`);
    // 路由 B（漏了 event 行）
    reply.raw.write(`data: ${JSON.stringify({ pct: 20 })}\n\n`);
    ```
  - Good:
    ```typescript
    // utils/sse.ts — 单点封装
    export function send(raw: NodeJS.WritableStream, event: string, data: unknown): void {
      raw.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
    }
    // 所有路由统一调用
    send(reply.raw, 'progress', { pct: 20 });
    ```
