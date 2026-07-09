# Rule Catalog — 错误处理

## Scope
- Covers: 外部调用错误转换、错误对象类型守卫、SSE 流错误推送、工具执行失败处理、状态文件损坏降级。
- 适用对象：所有 `services/api/` 下的 try/catch 逻辑、错误响应构造、SSE 错误事件、状态文件读写错误处理。

## Rules

### 外部错误须 try-catch 并转为用户友好消息
- Category: reliability
- Severity: critical
- Description: 调用外部服务（LLM API、文件系统、子进程）时，原始错误对象含内部细节且格式不可控。若直接透传给客户端，既不安全也难理解。必须 try-catch 后转为可读的友好消息，内部细节记入日志。
- Suggested fix: 在调用外部服务的边界统一 try-catch，记录原始错误，返回友好消息。
- Example:
  - Bad:
    ```typescript
    app.post('/run', async (request, reply) => {
      // 不 catch，外部错误直接透传，泄露内部细节且客户端难以理解
      const result = await engine.run(prompt);
      return reply.send(result);
    });
    ```
  - Good:
    ```typescript
    app.post('/run', async (request, reply) => {
      try {
        const result = await engine.run(prompt);
        return reply.send(result);
      } catch (err) {
        // 内部细节记日志，客户端只收友好消息
        request.log.error(err);
        const message = err instanceof Error ? err.message : '未知错误';
        return reply.code(500).send({ error: `引擎调用失败: ${message}` });
      }
    });
    ```

### err 须用 instanceof Error 守卫，禁止直接 String(err)
- Category: correctness
- Severity: critical
- Description: catch 块中的 `err` 类型是 `unknown`（TypeScript 严格模式）。直接 `String(err)` 或 `err.message` 不安全——若抛出的是非 Error 值（如字符串、对象），`String(err)` 可能得到 `[object Object]`，丢失信息。必须先用 `err instanceof Error` 守卫，再访问 `.message` / `.stack`。
- Suggested fix: 提供统一的错误信息提取函数，内部用 `instanceof Error` 守卫。
- Example:
  - Bad:
    ```typescript
    } catch (err) {
      // err 类型 unknown，String(err) 可能是 [object Object]
      const message = String(err);
      return reply.code(500).send({ error: message });
    }
    ```
  - Good:
    ```typescript
    function errMsg(err: unknown): string {
      // 守卫后才安全访问 .message，覆盖非 Error 抛出值
      return err instanceof Error ? err.message : String(err);
    }

    } catch (err) {
      request.log.error(err);
      return reply.code(500).send({ error: errMsg(err) });
    }
    ```

### SSE 流中错误须通过 error 事件推送，不能抛异常
- Category: reliability
- Severity: critical
- Description: SSE 流中抛异常会被 Fastify 捕获并以 JSON 错误响应回写，破坏 SSE 协议格式，客户端解析失败且丢失已产出事件的上下文。错误必须以 `error` 事件形式推送给客户端，再在 finally 中关闭连接。
- Suggested fix: SSE handler 的 try 块内捕获异常，调用 `send(reply.raw, 'error', { message })`，finally 中 `reply.raw.end()`。
- Example:
  - Bad:
    ```typescript
    app.get('/stream', async (request, reply) => {
      reply.raw.writeHead(200, sseHeaders);
      for await (const ev of adapter.run()) {
        send(reply.raw, ev.type, ev.data);
      }
      // 不 catch，异常破坏 SSE 协议
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
      } catch (err) {
        // 以 error 事件推送，保持 SSE 协议完整
        send(reply.raw, 'error', { message: errMsg(err) });
      } finally {
        reply.raw.end();
      }
    });
    ```

### 工具执行失败须 catch 并返回错误描述给 LLM，不中断循环
- Category: reliability
- Severity: critical
- Description: workflow 循环中调用工具（文件读写、子进程等）时，单个工具失败不应中断整个循环——LLM 拿到错误描述后可自行调整策略重试。若直接抛异常中断，已产出结果丢失，且 LLM 无机会纠错。必须 catch 单步错误，把错误描述作为结果返回给 LLM。
- Suggested fix: 在工具调用外层 catch，将错误转为结构化结果返回，continue 循环。
- Example:
  - Bad:
    ```typescript
    for (const step of steps) {
      // 不 catch，单步失败中断整个循环，已产出结果丢失
      const result = await tool.run(step);
      yield { type: 'result', data: result };
    }
    ```
  - Good:
    ```typescript
    for (const step of steps) {
      try {
        const result = await tool.run(step);
        yield { type: 'result', data: result };
      } catch (err) {
        // 把错误描述返回给 LLM，让其有机会纠错重试，不中断循环
        yield { type: 'result', data: { error: errMsg(err), step } };
      }
    }
    ```

### 状态文件损坏须优雅降级，不能崩溃服务
- Category: reliability
- Severity: critical
- Description: `FileStateStore` 读取的 JSON 状态文件可能因进程崩溃写入不完整、并发写交错而损坏（解析失败）。若直接抛异常，会导致依赖状态的接口全部不可用，服务整体崩溃。必须 catch 解析错误，降级为"状态未知"并重建空状态，服务继续运行。
- Suggested fix: 读取状态文件时 try-catch JSON.parse，失败时返回默认状态并记录告警。
- Example:
  - Bad:
    ```typescript
    async read(runId: string): Promise<RunState> {
      const raw = await fs.readFile(this.pathOf(runId), 'utf-8');
      // JSON.parse 失败会抛异常，调用方可能崩溃
      return JSON.parse(raw) as RunState;
    }
    ```
  - Good:
    ```typescript
    async read(runId: string): Promise<RunState> {
      try {
        const raw = await fs.readFile(this.pathOf(runId), 'utf-8');
        return JSON.parse(raw) as RunState;
      } catch (err) {
        // 文件损坏时降级为默认状态，服务继续运行
        console.warn(`状态文件损坏，降级处理: ${runId}`, errMsg(err));
        return { stage: 'unknown', draft: true };
      }
    }
    ```
