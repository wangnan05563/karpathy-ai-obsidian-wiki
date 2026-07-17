# Rule Catalog — 配置管理

## Scope
- Covers: 后端可编辑配置的恢复接口、运行时实例同步、字段级重置、预设集中管理、配置接口生命周期。
- 适用对象：`routes/` 目录下的配置类路由（如 `/api/ai/config`、`/api/ai/reset-config`）、配置持久化逻辑、adapter 运行时实例同步逻辑、预设常量定义。

## Rules
### 可编辑配置必须提供恢复默认值接口
- Category: maintainability
- Severity: critical
- Description: 凡是暴露给前端可编辑的配置（如 LLM 的 provider/baseUrl/model/apiKey），都必须提供"恢复默认值"接口。只有保存接口没有恢复接口，用户一旦填错或遗忘原值，只能手动翻代码找默认配置，且错误配置可能持续生效导致服务不可用。恢复接口须调用 `defaultConfig()`（或等价函数）重置到出厂默认值，让用户拥有一键回退能力。
- Suggested fix: 在已有 GET/PUT 配置接口的路由文件中，新增 `POST /api/{module}/reset-config` 接口，调用 `defaultConfig()` 重置配置并同步 adapter。
- Example:
  - Bad:
    ```typescript
    // 只提供保存接口，用户改错后无法一键回退，只能手动改 config.json
    app.put('/api/ai/config', async (request, reply) => {
      const newConfig = request.body as AiConfig;
      await fs.writeFile('config.json', JSON.stringify(newConfig));
      return reply.send({ ok: true });
    });
    ```
  - Good:
    ```typescript
    // 提供保存接口
    app.put('/api/ai/config', async (request, reply) => {
      const newConfig = request.body as AiConfig;
      await fs.writeFile('config.json', JSON.stringify(newConfig));
      return reply.send({ ok: true });
    });

    // 提供恢复默认值接口，用户改错可一键回退
    app.post('/api/ai/reset-config', async (request, reply) => {
      const defaults = defaultConfig();
      await fs.writeFile('config.json', JSON.stringify(defaults));
      return reply.send({ ok: true, config: defaults });
    });
    ```
### 配置恢复须同步运行时实例
- Category: correctness
- Severity: critical
- Description: 配置恢复接口若只写 `config.json` 而不调用 `adapter.updateConfig()`，会导致文件已重置但运行时 adapter 仍持有旧配置，下一次引擎调用仍用错误配置，"恢复"形同虚设。配置恢复必须同时完成两件事：持久化新值到配置文件 + 同步更新运行时 adapter 实例。
- Suggested fix: 在 reset 接口中，写完配置文件后立即调用 `adapter.updateConfig()` 传入新配置，确保运行时实例与持久化配置一致。
- Example:
  - Bad:
    ```typescript
    app.post('/api/ai/reset-config', async (request, reply) => {
      const defaults = defaultConfig();
      // 只写文件，不同步 adapter，运行时仍用旧配置
      await fs.writeFile('config.json', JSON.stringify(defaults));
      return reply.send({ ok: true });
    });
    ```
  - Good:
    ```typescript
    app.post('/api/ai/reset-config', async (request, reply) => {
      const defaults = defaultConfig();
      await fs.writeFile('config.json', JSON.stringify(defaults));
      // 同步运行时 adapter，确保下一次调用即生效
      adapter.updateConfig({
        provider: defaults.llm.provider,
        baseUrl: defaults.llm.baseUrl,
        model: defaults.llm.model,
        apiKey: defaults.llm.apiKey,
      });
      return reply.send({ ok: true, config: defaults });
    });
    ```
### 配置恢复须仅重置目标字段
- Category: correctness
- Severity: critical
- Description: 配置文件通常包含多个模块（如 `llm`、`vault`、`engine`）。若 reset 接口用 `defaultConfig()` 整体覆盖 `config.json`，会把其他模块的配置一并重置，用户对其他模块的定制全部丢失。必须只重置目标模块字段，保留其余字段原值。
- Suggested fix: 使用对象展开合并：读取当前配置与默认配置，仅替换目标模块字段（如 `{...current, llm: {...defaults.llm}}`），其余字段保留当前值。
- Example:
  - Bad:
    ```typescript
    app.post('/api/ai/reset-config', async (request, reply) => {
      const defaults = defaultConfig();
      // 整体覆盖，vault/engine 等其他模块配置全部丢失
      await fs.writeFile('config.json', JSON.stringify(defaults));
      return reply.send({ ok: true });
    });
    ```
  - Good:
    ```typescript
    app.post('/api/ai/reset-config', async (request, reply) => {
      const current = JSON.parse(await fs.readFile('config.json', 'utf-8'));
      const defaults = defaultConfig();
      // 仅重置 llm 字段，保留其他模块配置
      const next = { ...current, llm: { ...defaults.llm } };
      await fs.writeFile('config.json', JSON.stringify(next));
      return reply.send({ ok: true, config: next });
    });
    ```
### 预设列表须集中管理
- Category: maintainability
- Severity: suggestion
- Description: 预设列表（如 LLM provider 预设、模型预设）若散落在多个路由文件中，会导致新增预设需改多处、修改预设易遗漏，且无法被前端与后端共享引用。预设列表必须集中定义在单一常量中，供所有路由与前端引用。
- Suggested fix: 将预设列表集中定义为路由文件中的常量（如 `routes/ai.ts` 的 `LLM_PRESETS`），所有引用方从此常量读取。
- Example:
  - Bad:
    ```typescript
    // routes/ai.ts 内联预设
    app.get('/api/ai/presets', async () => [
      { provider: 'openai', model: 'gpt-4' },
      { provider: 'anthropic', model: 'claude-3' },
    ]);

    // routes/other.ts 又重复定义一份预设，两处不同步
    app.get('/api/other/presets', async () => [
      { provider: 'openai', model: 'gpt-4' },
    ]);
    ```
  - Good:
    ```typescript
    // 预设集中定义在单一常量，所有引用方从此读取
    export const LLM_PRESETS = [
      { provider: 'openai', model: 'gpt-4' },
      { provider: 'anthropic', model: 'claude-3' },
    ] as const;

    app.get('/api/ai/presets', async () => LLM_PRESETS);
    ```
### 配置接口须有完整生命周期
- Category: best-practices
- Severity: suggestion
- Description: 配置接口若只有 GET（读取）+ PUT（保存），用户无法验证配置是否可用，也无法一键回退默认值，配置错误的调试成本高。完整配置接口应覆盖读取、保存、恢复、测试连接四个动作，让用户在不离开配置页面的情况下完成"改 → 测 → 回退"闭环。
- Suggested fix: 配置类路由应提供四类接口：`GET /api/{module}/config`（读取）、`PUT /api/{module}/config`（保存）、`POST /api/{module}/reset-config`（恢复默认）、`POST /api/{module}/test-connection`（测试连接）。
- Example:
  - Bad:
    ```typescript
    // 只有读取和保存，用户改错后无法测试也无法回退
    app.get('/api/ai/config', async () => readConfig());
    app.put('/api/ai/config', async (request) => saveConfig(request.body));
    ```
  - Good:
    ```typescript
    // 完整生命周期：读取 + 保存 + 恢复 + 测试
    app.get('/api/ai/config', async () => readConfig());
    app.put('/api/ai/config', async (request) => saveConfig(request.body));
    app.post('/api/ai/reset-config', async () => resetConfig());
    app.post('/api/ai/test-connection', async (request) => testConnection(request.body));
    ```
