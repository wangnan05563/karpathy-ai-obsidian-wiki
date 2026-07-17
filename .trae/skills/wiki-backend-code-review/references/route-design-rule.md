# Rule Catalog — 路由设计

## Scope
- Covers: Fastify 路由的注册方式、参数校验、Content-Type 分发、handler 职责边界、响应格式约定。
- 适用对象：`routes/` 目录下的路由注册函数、handler 实现、请求参数解析逻辑。

## Rules
### 路由参数须校验类型/必填/格式，无效返回 400
- Category: correctness
- Severity: critical
- Description: 路由参数（query / params / body）若不校验，非法输入会一路传到 workflow/engine，引发难以定位的深层错误，甚至路径遍历。必须在路由层第一时间校验，无效时返回 400 并附带可读的错误描述，让调用方快速定位问题。
- Suggested fix: 使用 Fastify schema 校验或显式守卫校验；错误响应统一包含 `error` 字段与人类可读描述。
- Example:
  - Bad:
    ```typescript
    app.post('/run', async (request, reply) => {
      // 直接取 body 字段，不校验类型/必填，非法值会引发深层错误
      const prompt = request.body.prompt;
      const result = await workflow.run(prompt);
      return result;
    });
    ```
  - Good:
    ```typescript
    app.post('/run', async (request, reply) => {
      const body = request.body as { prompt?: unknown };
      if (typeof body.prompt !== 'string' || body.prompt.length === 0) {
        // 第一时间返回 400，阻止非法值进入 workflow
        return reply.code(400).send({ error: 'prompt 必须为非空字符串' });
      }
      const result = await workflow.run(body.prompt);
      return reply.send(result);
    });
    ```
### Content-Type 须显式分发（multipart vs json）
- Category: correctness
- Severity: critical
- Description: 同一路由可能同时接收 `multipart/form-data`（上传文件）和 `application/json`（纯参数）请求。若不显式判断 Content-Type，用 multipart parser 处理 json 或反之，会抛出难以理解的解析错误。必须根据 `request.headers['content-type']` 分发到不同处理分支。
- Suggested fix: 在 handler 入口判断 Content-Type，分别走 multipart 与 json 解析路径。
- Example:
  - Bad:
    ```typescript
    app.post('/upload', async (request, reply) => {
      // 不判断 Content-Type，multipart 请求会被当作 json 解析，直接报错
      const data = request.body as { content: string };
      await vault.write(data.content);
      return reply.send({ ok: true });
    });
    ```
  - Good:
    ```typescript
    app.post('/upload', async (request, reply) => {
      const ct = request.headers['content-type'] ?? '';
      if (ct.startsWith('multipart/form-data')) {
        const file = await request.file();
        if (!file) return reply.code(400).send({ error: '缺少文件' });
        await vault.write(await file.toBuffer());
      } else if (ct.includes('application/json')) {
        const body = request.body as { content: string };
        if (!body?.content) return reply.code(400).send({ error: '缺少 content' });
        await vault.write(body.content);
      } else {
        return reply.code(415).send({ error: `不支持的 Content-Type: ${ct}` });
      }
      return reply.send({ ok: true });
    });
    ```
### 路由注册函数签名须统一为 (app, adapter) => void
- Category: maintainability
- Severity: critical
- Description: 路由注册函数若签名不统一（有的传 app，有的传 server，有的传 adapter，有的不传），会导致装配层无法用统一方式注册所有路由，且难以在测试中注入 mock adapter。必须统一为 `(app: FastifyInstance, adapter: EngineAdapter) => void`。
- Suggested fix: 所有路由注册函数遵循同一签名，adapter 通过参数注入而非全局单例获取。
- Example:
  - Bad:
    ```typescript
    // 路由 A
    export function registerRunRoute(app: FastifyInstance) { ... }
    // 路由 B（签名不一致，且从全局取 adapter）
    export function registerQueryRoute(server: FastifyInstance, opts: { adapter?: EngineAdapter }) {
      const adapter = opts.adapter ?? globalAdapter;
      ...
    }
    ```
  - Good:
    ```typescript
    // 统一签名，adapter 显式注入，便于测试 mock
    export function registerRunRoute(app: FastifyInstance, adapter: EngineAdapter): void {
      app.post('/run', async (request, reply) => {
        const result = await adapter.run(request.body);
        return reply.send(result);
      });
    }

    export function registerQueryRoute(app: FastifyInstance, adapter: EngineAdapter): void {
      app.get('/query', async (request, reply) => {
        const result = await adapter.query(request.query);
        return reply.send(result);
      });
    }
    ```
### GET 路由返回 JSON，POST 长任务返回 SSE
- Category: best-practices
- Severity: suggestion
- Description: HTTP 语义上 GET 应为幂等、短查询，返回 JSON 即可；POST 长任务（编译、批量生成）耗时长，应返回 SSE 实时推送进度，避免客户端长时间等待无反馈。混用会导致客户端无法预期能力（如对 SSE 接口发 GET，或对 JSON 接口期望流式）。
- Suggested fix: 短查询用 GET + JSON；耗时任务用 POST + SSE，并在路由命名/文档中明示。
- Example:
  - Bad:
    ```typescript
    // 编译是长任务却用 GET 返回 JSON，客户端无进度反馈
    app.get('/compile', async (request, reply) => {
      const result = await adapter.compile(); // 可能跑几十秒
      return reply.send(result);
    });
    ```
  - Good:
    ```typescript
    // 短查询用 GET + JSON
    app.get('/status/:runId', async (request, reply) => {
      const { runId } = request.params as { runId: string };
      return reply.send(await adapter.status(runId));
    });

    // 长任务用 POST + SSE，实时推送进度
    app.post('/compile', async (request, reply) => {
      reply.raw.writeHead(200, sseHeaders);
      try {
        for await (const ev of adapter.compile()) {
          send(reply.raw, ev.type, ev.data);
        }
      } finally {
        reply.raw.end();
      }
    });
    ```
### 路由层不写业务逻辑，只做参数解析 + 调用 + 格式化
- Category: maintainability
- Severity: critical
- Description: 路由 handler 若混入业务逻辑（如直接操作文件、编排多步骤、做领域决策），会导致逻辑无法复用、难以测试，且路由文件膨胀。路由层应只负责：解析参数、校验、调用 workflow/adapter、格式化响应。业务逻辑下沉到 workflow / engine / vault 层。
- Suggested fix: 将 handler 中的业务步骤提取到 workflow 函数，handler 只保留"解析 → 调用 → 格式化"三步。
- Example:
  - Bad:
    ```typescript
    app.post('/run', async (request, reply) => {
      const { prompt } = request.body as { prompt: string };
      // 业务逻辑全堆在 handler 里：读 schema、调引擎、写文件、更新索引
      const schema = await fs.readFile('SCHEMA.md', 'utf-8');
      const result = await engine.run(prompt, schema);
      await fs.writeFile(path.join(vaultRoot, 'note.md'), result);
      await appendIndex('note');
      return reply.send({ ok: true });
    });
    ```
  - Good:
    ```typescript
    app.post('/run', async (request, reply) => {
      const { prompt } = request.body as { prompt: string };
      if (!prompt) return reply.code(400).send({ error: '缺少 prompt' });
      // handler 只做：解析 → 调用 → 格式化，业务逻辑在 workflow
      const result = await workflow.run(prompt);
      return reply.send(result);
    });
    ```
