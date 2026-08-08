# BYOK 多用户密钥代理规则（Bring Your Own Key / 配置随请求下发 + 覆盖）

**代码**：CODING-BYOK
**严重级别**：critical

## 问题（Problem）

多用户应用中，若所有用户共用服务端一份 LLM / 搜索 / 工具配置（含 API Key），会出现：① 全员共用同一额度 → 彼此限流；② 任一用户配置错误影响所有人；③ 密钥落在服务端磁盘 / 日志，泄露面扩大。

我们采用的架构是 **BYOK（Bring Your Own Key）代理**：每个用户在前端本地（IndexedDB，按 userId 命名空间）保存自己的 provider / baseUrl / apiKey / model 等配置；每次请求（如 `/api/query`）由前端把**当前用户**的配置随请求体带上，后端用其**覆盖**服务端共享配置后再调用 harness；密钥仅经请求体一次性下发，**不落服务端磁盘、不回显 GET、不记日志**。

> 真实踩坑：① 前端曾始终下发 `toolsConfig`（含默认空对象）→ 后端整体替换服务端共享 MCP / CLI → 未配置工具的用户工具能力被清空。修复为「仅当用户实际配置了工具才下发」，后端再加防御（空工具配置视为未提供、回退服务端共享）。② 网关门禁最初只校验 apiKey，畸形 provider / baseUrl / model 透传到 harness 触发 500；加固为缺任一即 400。

## 规则（Rule）

### R-1：每用户配置本地命名空间隔离，密钥绝不落服务端

每用户的 AI / 搜索 / 工具配置存前端本地（IndexedDB `preferences`，键内化 userId → `usercfg::<kind>::<userId>`），天然按用户隔离；密钥仅经请求体一次性下发，**后端不得写入磁盘、不得回显 GET、不得记入日志**。服务端不保留任何用户默认（强制每用户各自配置）。

```typescript
// 前端 services/userConfig.ts（按用户命名空间读写，不回传服务端）
export async function loadAiUserConfig(userId: string) {
  return chatDb.get('preferences', `usercfg::ai::${userId}`);
}
// 后端 routes/query.ts：密钥只从请求体取，绝不持久化
const override = body.llmConfig; // 仅本次请求使用，从不写盘
```

### R-2：缺少必需密钥不得回落服务端共享（强制每用户配置）

未填 API Key 的请求直接 **400**，不允许回落到服务端共享密钥（杜绝全员共用同一额度 / 互现限流）。provider / baseUrl / model 同样须非空，畸形配置不透明透传到 harness（避免 500）。

```typescript
// 后端 routes/query.ts
if (!body.llmConfig?.apiKey || !body.llmConfig?.provider ||
    !body.llmConfig?.baseUrl || !body.llmConfig?.model) {
  return reply.code(400).send({
    error: '请在「配置→AI 服务」填写你的 API Key / provider / baseUrl / model',
  });
}
```

### R-3：覆盖须纯函数、空覆盖不得清空服务端共享

覆盖逻辑抽为**纯函数** `applyPerRequestOverride(harnessConfig, webSearchConfig, toolsConfig, override)`（仅 type-only import，便于单测）；整体替换须谨慎——**空 / 默认工具配置视为「未提供覆盖」，回退服务端共享配置**，绝不能把服务端共享 MCP / CLI 清空。

```typescript
// 后端 engine/byok-override.ts（纯函数，运行时零依赖）
export function applyPerRequestOverride(harness, web, tools, override) {
  const eff = { ...harness };
  if (override?.llmConfig) eff.llm = { ...harness.llm, ...override.llmConfig, apiKeyRef: override.llmConfig.apiKeyRef };
  if (override?.searchConfig) eff.webSearch = { ...web, ...override.searchConfig };
  if (override?.toolsConfig && hasRealTools(override.toolsConfig)) eff.tools = override.toolsConfig; // 空则保留服务端共享
  return eff;
}
```

## 适用 / 不适用

- **适用**：多用户 SaaS / 桌面应用、需用户自带 API Key 的 LLM / 搜索 / 工具代理、要求密钥不落服务端的场景、CI 密钥隔离回归。
- **不适用**：单用户应用（无多租户隔离需求）、密钥本就该服务端统一托管且用户无自带需求的场景。

## 检查清单

- [ ] 每用户配置是否存前端本地命名空间（`byok_per_user_override.byok_user_config_namespaces` 列出的 `usercfg::<kind>::<userId>` 等），不跨用户共享
- [ ] 密钥是否仅经请求体下发，后端不落盘 / 不回显 GET / 不记日志（`byok_per_user_override.secret_not_persisted`）
- [ ] 缺 apiKey（及 provider / baseUrl / model）是否直接 400，不回落服务端共享（`byok_per_user_override.require_key_no_fallback`）
- [ ] 覆盖是否为纯函数、空覆盖不清空服务端共享配置（`byok_per_user_override.override_must_be_pure` / `empty_override_falls_back`）
- [ ] 前端是否仅当用户实际配置了对应能力才下发对应配置块（避免空对象清空服务端能力）
