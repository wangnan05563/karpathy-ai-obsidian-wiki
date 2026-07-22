# Rule Catalog — 配置化参数与持久化边界（后端审查视角）

> 本规则文件基于「配置化参数硬编码、路径解析漂移、缓存刷新缺失、跨 origin 持久化分离」等历史问题复盘提炼，
> 对应编码规范中的配置化原则（见 wiki-code-dev）。
> 所有参数从 [config/review-config.md](../config/review-config.md) 的"配置化与持久化边界审查参数（config_persistence_boundary）"节读取，
> 规则文件不硬编码任何具体路径、正则或函数名。
>
> 注：路径解析锚点（BR-035）与缓存刷新机制（BR-036）的详细实现示例见
> [persistence-cache-rule.md](persistence-cache-rule.md) 的 PC-1 / PC-2 规则，
> 本文件从"配置化参数与持久化边界"整合视角补充审查要点。

## Scope

- Covers: 硬编码可配置参数检测、路径解析锚点合规性、缓存刷新机制、跨 origin 持久化边界
- 适用对象：所有 `api/` 下涉及配置持久化、文件落盘、内存缓存、HTTP 路由参数到文件系统映射的代码
- Does NOT cover: 通用路径遍历防护（见 [security-rule.md](security-rule.md)）、配置类路由生命周期（见 [config-management-rule.md](config-management-rule.md)）、会话状态缓存失效（见 [session-state-rule.md](session-state-rule.md)）、写盘函数实现细节（见 [persistence-cache-rule.md](persistence-cache-rule.md)）

## Rules

### BR-034 配置化参数检测

- Category: config-persistence-boundary
- Severity: critical
- Description: 后端代码中禁止硬编码可配置参数（`configurable_param_patterns`：API Key / port / path / timeout / secret / 白名单），必须通过 `config.json` 或环境变量注入。硬编码这些参数会导致环境切换时无法配置、密钥泄露到代码仓库、端口冲突无法调整等问题。
- Check patterns:
  - `process.env.` — 确认密钥从环境变量读取，而非字面量
  - `app.listen(` — 确认 port/host 从 config 读取
  - `path.join(` — 确认路径从 config 读取，而非硬编码字符串
  - `new Set([` — 确认白名单从 config 读取，而非内联数组
- Suggested fix: 将硬编码值迁移到 `config.json` 对应字段，或通过 `process.env[config.xxxRef]` 读取环境变量。

### BR-035 路径解析锚点合规性

- Category: config-persistence-boundary
- Severity: critical
- Description: 路径解析必须采用三级策略（`path_resolution_strategy`：优先 `import.meta.url` + 打包兜底 `process.cwd()` + CWD 探测），禁止 `process.cwd()` 作为唯一路径锚点。CWD 受启动方式影响（开发模式、打包模式、工具链切换、IDE 集成），作为唯一锚点会导致配置文件找不到或写到错误位置。
- Check: `getConfigPath()` / `getStateDir()` 等路径解析函数必须实现三级策略，主锚点为 `path.dirname(fileURLToPath(import.meta.url))`。
- Suggested fix: 参见 [persistence-cache-rule.md](persistence-cache-rule.md) 的 PC-1 规则示例代码。

### BR-036 缓存刷新机制

- Category: config-persistence-boundary
- Severity: critical
- Description: 配置类写盘函数（如 `saveAiConfig` / `resetAiConfig` / `saveWebSearchConfig`）在 `await fs.writeFile(...)` 成功后必须立即调用对应的缓存刷新方法（如 `refreshConfigCache(data)`），同步更新 `configCache.data` / `.path` / `.loadedAt`。TTL 不替代显式刷新——TTL 是兜底机制，写盘后必须立即同步缓存，避免窗口期内 GET 返回旧值。
- Check: 所有写盘函数在 `await fs.writeFile(...)` 成功后、`return reply` 之前必须调用对应的缓存刷新方法；`writeFile` 抛错时不得刷新缓存（保持旧值供降级读取）。
- Suggested fix: 参见 [persistence-cache-rule.md](persistence-cache-rule.md) 的 PC-2 规则示例代码。

### BR-037 跨 origin 持久化边界

- Category: config-persistence-boundary
- Severity: critical
- Description: 跨 origin 持久化数据（`cross_origin_data_types`：AI 配置 apiKey / 历史会话）必须后端为权威源，前端浏览器存储（localStorage / IndexedDB）仅作降级缓存。后端必须提供 CRUD 路由（如 `/api/conversations/:id`）；后端不可用时前端降级到本地缓存，但须 `console.warn` 记录降级事件，不得静默失败。localStorage 仅存储非敏感 UI 状态（baseUrl / model），API key 必须存储在 backend config.json。
- Check:
  - 跨 origin 列为"是"的数据，后端必须提供 CRUD 路由
  - 前端以后端为权威源、浏览器存储仅作降级缓存
  - 降级时须 `console.warn` 记录，不得静默失败
  - localStorage 不得存储 API key 等敏感信息
- Suggested fix: 将敏感数据迁移到后端 config.json，前端 localStorage 仅保留 baseUrl / model 等非敏感 UI 状态；为跨 origin 数据实现后端 CRUD 路由。
