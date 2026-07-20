# Rule Catalog — 敏感字段脱敏

## Scope

- Covers: 后端配置类 GET 接口返回敏感字段（API Key / authtoken / password / secret）时必须脱敏，POST/PUT 接口接收空串表示"不修改"。
- 适用对象：所有返回或接收敏感配置字段的路由 handler、序列化函数、配置读取逻辑。
- Does NOT cover: 非敏感公开字段（如 provider / baseUrl / model）；内部调试接口（仅限开发环境且不返回生产密钥）；日志中的脱敏（由 [security-rule.md](security-rule.md) 的"错误信息不泄露内部路径/堆栈"覆盖）。

> 所有敏感字段名模式、脱敏策略、空串语义均从 [config/review-config.md](../config/review-config.md) 的"敏感字段脱敏参数"节读取，本规则文件不硬编码任何具体值。

## Rules

### SFM-1 GET 接口返回敏感字段必须脱敏，POST 空串表示不修改

- Category: security
- Severity: critical
- Description: 配置类 GET 接口（如 `GET /api/ai/config`、`GET /api/tunnel/config`）若直接返回 `apiKey` / `authtoken` / `password` / `secret` 明文，前端代码、浏览器 DevTools、网络代理日志、CDN 缓存都会留存密钥副本，一旦泄露即获得原始凭据。必须对敏感字段脱敏后返回，并附 `configured` 标志让前端知道"是否已配置"。对应地，POST/PUT 接口接收空串表示"不修改该字段"——避免前端为保留原密钥而必须先 GET 再 PUT 明文，进一步减少密钥在网络上传输的次数。
- Judgment logic:
  1. 用 `Grep` 检索路由文件中的 GET handler（`app.get` / `reply.send`），扫描返回对象字段名是否匹配 `sensitive_field_patterns`（如 `key|token|secret|password|authtoken`）。
  2. 命中的字段必须经过 `mask()` 函数处理（按 `mask_strategy` 默认 `last4_padstart`：保留末 4 位，前缀用 `****` 填充），且附带 `<field>_configured: boolean` 标志。
  3. 对 POST/PUT handler，扫描 body 解构是否包含敏感字段——若 `body.<field> === ''` 必须跳过更新（`empty_string_semantics` 默认 `no_change`），仅当非空串才覆盖。
  4. 验证 GET 返回的对象中不存在任何明文敏感字段（即使 `configured: false` 也不应返回原始值，统一返回空串或 `null` + 标志）。
- Applicable scenarios: 所有配置类 GET 接口（LLM apiKey / tunnel authtoken / database password / OAuth secret）；前端配置页面回显场景；移动端通过 API 读取配置的场景。
- Not applicable: 非敏感公开字段（provider / baseUrl / model / port）；仅限开发环境的调试接口（须返回明文时必须额外鉴权与日志告警）；服务端内部传递（不通过 HTTP 返回）。
- Configuration parameters: 见 [config/review-config.md](../config/review-config.md) 的"敏感字段脱敏参数"节——`sensitive_field_patterns` / `mask_strategy` / `empty_string_semantics`。
- Suggested fix: 提供统一的 `maskSecret(value: string): string` 与 `isConfigured(value: string): boolean` 工具函数；GET handler 返回脱敏值 + configured 标志；POST handler 用 `if (body.<field>) config.<field> = body.<field>` 跳过空串。
- Example:
  - Bad:
    ```typescript
    // GET /api/ai/config —— 直接返回明文 apiKey
    app.get('/api/ai/config', async () => {
      const config = await readConfig();
      return config; // apiKey 明文暴露给前端/代理日志/DevTools
    });

    // PUT /api/ai/config —— 空串覆盖原密钥
    app.put('/api/ai/config', async (request) => {
      const body = request.body as { apiKey: string };
      const config = await readConfig();
      // body.apiKey 为空串时直接覆盖，原密钥丢失
      config.apiKey = body.apiKey;
      await writeConfig(config);
    });
    ```
  - Good:
    ```typescript
    function maskSecret(value: string): string {
      if (!value) return '';
      // last4_padstart: 保留末 4 位，前缀 ****
      const tail = value.slice(-4);
      return '****' + tail;
    }

    // GET /api/ai/config —— 返回脱敏值 + configured 标志
    app.get('/api/ai/config', async () => {
      const config = await readConfig();
      return {
        ...config,
        apiKey: maskSecret(config.apiKey),
        apiKey_configured: Boolean(config.apiKey),
      };
    });

    // PUT /api/ai/config —— 空串 = 不修改，非空串才覆盖
    app.put('/api/ai/config', async (request) => {
      const body = request.body as { apiKey?: string };
      const config = await readConfig();
      // empty_string_semantics: no_change —— 空串跳过，仅非空才更新
      if (body.apiKey) {
        config.apiKey = body.apiKey;
      }
      await writeConfig(config);
    });
    ```
- Checklist:
  - [ ] 所有 GET handler 返回的对象中，匹配 `sensitive_field_patterns` 的字段均经过 `mask()` 处理。
  - [ ] 每个脱敏字段附带 `<field>_configured: boolean` 标志，前端可判断是否已配置。
  - [ ] POST/PUT handler 中敏感字段为空串时跳过更新，不覆盖原值。
  - [ ] `mask_strategy` 与 `empty_string_semantics` 从 config 读取，规则文件不硬编码。
- Related rules: API Key 仅通过环境变量引用见 [security-rule.md](security-rule.md) 的"API Key 仅通过环境变量引用"；配置接口完整生命周期见 [config-management-rule.md](config-management-rule.md)。
