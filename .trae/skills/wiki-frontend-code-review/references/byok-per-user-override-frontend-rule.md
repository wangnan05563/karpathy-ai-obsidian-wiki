# Rule Catalog — BYOK Per-User Config Override (Frontend)

前端 BYOK（Bring Your Own Key）多用户配置代理审查规则：确保每用户配置在客户端按 userId 命名空间隔离、密钥仅经请求体一次性下发（不落服务端 / 不回显 / 不记日志）、前端仅当配置存在才下发对应块、配置菜单访问门控正确。所有参数从 `config/review-config.md` 读取，禁止在规则文件中硬编码。

> 复盘来源：多用户应用若共用服务端一份 LLM / 搜索 / 工具配置（含 API Key），会全员共用额度互现限流、密钥落服务端泄露面扩大。架构改为前端本地（IndexedDB 按 userId 命名空间）保存每用户配置，每次请求随 body 带当前用户配置，后端覆盖服务端共享配置后调用 harness，密钥仅经请求体下发、不落盘 / 不回显 GET / 不记日志。真实踩坑：前端曾始终下发空 `toolsConfig` → 后端整体替换清空服务端共享工具能力；网关门禁只校验 apiKey，畸形 provider / baseUrl / model 透传触发 500。

## Scope
- Covers: `frontend/src/services/**/userConfig.ts`（按用户命名空间读写）、`frontend/src/views/Config.vue`（配置菜单访问门控 + 个人配置读写）、`frontend/src/views/Query.vue`（随请求注入当前用户配置）、`frontend/src/stores/**`（per-user config load/persist）。
- Does NOT cover: 纯服务端密钥托管（无多租户自带需求）、单用户应用、密钥服务端统一托管且用户无自带需求场景。

## Rules

### FR-070-1: 每用户配置本地命名空间隔离，不跨用户共享

IsUrgent: True
Category: BYOK / Per-User Override

#### Description

每用户的 AI / 搜索 / 工具配置必须存前端本地（IndexedDB `preferences`，键内化 userId，如 `usercfg::<kind>::<userId>`），按下发用户命名空间读写，**绝不**用全局 `localStorage` 或跨用户共享的存储（那会造成配置泄漏：用户 A 的配置被用户 B 读到）。应用层只读取当前登录用户命名空间。

#### Suggested Fix

```typescript
// services/userConfig.ts — 键内化 userId，天然隔离
export async function loadAiUserConfig(userId: string) {
  return chatDb.get('preferences', `usercfg::ai::${userId}`); // 仅当前用户命名空间
}
export async function saveAiUserConfig(userId: string, cfg: AiUserConfig) {
  await chatDb.put('preferences', { key: `usercfg::ai::${userId}`, ...cfg });
}
```

> **示例代码**: 见 config-isolation-rule.md（多实例配置命名空间隔离）与 runtime-data-privacy-frontend-rule.md（FR-063，客户端持久化按 ownerId）。

### FR-070-2: 密钥仅经请求体下发，仅当配置存在才下发对应块

IsUrgent: True
Category: BYOK / Per-User Override

#### Description

前端每次请求须注入**当前用户**的 provider / baseUrl / apiKey / model 等；密钥仅经请求体（POST body）下发，**禁止**放进 URL 查询参数 / GET 接口 / 前端日志 / 控制台。且必须是「仅当用户实际配置了对应能力才下发对应配置块」——始终下发空 `toolsConfig` 会让后端整体替换、清空服务端共享工具能力（真实事故）。

#### Suggested Fix

```typescript
// views/Query.vue — 构造请求体时按实际配置注入
const ai = await loadAiUserConfig(uid);
if (ai?.apiKey) payload.llmConfig = { provider: ai.provider, baseUrl: ai.baseUrl, model: ai.model, apiKey: ai.apiKey };
const tools = await loadToolsUserConfig(uid);
if (hasRealTools(tools)) payload.toolsConfig = tools; // 仅配置了才下发，避免清空服务端共享
```

> **示例代码**: 见 runtime-data-privacy-frontend-rule.md（FR-063，密钥不回显 GET）与 sensitive-field-display-rule.md（敏感字段不展示）。

### FR-070-3: 配置菜单访问门控（敏感 admin ↔ 个人 BYOK）

IsUrgent: False
Category: BYOK / Per-User Override

#### Description

RBAC 仅 `admin` 有 `config` 权限，普通用户看不到「配置」菜单 → 非管理员无法打开个人 BYOK 设置（违背「各用户可改自身配置」）。修复：`App.vue` 配置菜单项 `permission` 改为 `'dashboard'`（全员可见），`Config.vue` 内对敏感 tab（SCHEMA / 系统 / AI 服务 / 工具 / QQ 导入 / Prompt IDE）加 `v-if="isAdmin"` 二次拦截，非管理员默认切到个人配置 tab；`onMounted` 中敏感数据加载仅 `isAdmin` 时执行。后端 admin PUT 端点本就需权限，UI 再拦双保险。

#### Suggested Fix

```vue
<!-- App.vue：菜单全员可见 -->
<el-menu-item v-permission="'dashboard'" index="/config">配置</el-menu-item>
<!-- Config.vue：敏感 tab 二次拦截 -->
<el-tab-pane v-if="isAdmin" name="schema" label="SCHEMA 规范">...</el-tab-pane>
<script setup> onMounted(() => { if (isAdmin) loadSchema(); }); </script>
```

> **示例代码**: 见 config-isolation-rule.md（配置按用户隔离）与 runtime-data-privacy-frontend-rule.md（FR-063）。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `byok_per_user_override_frontend.enabled` | `true` | 启用本组规则（FR-070） |
| `byok_per_user_override_frontend.severity_namespace_isolation` | `critical` | FR-070-1 每用户配置未本地命名空间隔离违规级别 |
| `byok_per_user_override_frontend.severity_secret_in_body` | `critical` | FR-070-2 密钥未仅经请求体下发 / 始终下发空块违规级别 |
| `byok_per_user_override_frontend.severity_menu_gate` | `suggestion` | FR-070-3 配置菜单访问门控违规级别 |
| `byok_per_user_override_frontend.user_config_namespaces` | `usercfg::ai::,usercfg::search::,usercfg::tools::` | 按用户命名空间键前缀（键内化 userId） |
| `byok_per_user_override_frontend.config_menu_permission` | `dashboard` | 配置菜单项的可见权限（全员） |
| `byok_per_user_override_frontend.admin_only_tabs` | `schema,system,ai-service,tools,qq-import,prompt-ide` | 仅管理员可见的敏感 tab |
| `byok_per_user_override_frontend.secret_fields` | `apiKey` | 仅经请求体下发、禁止回显/日志的敏感字段 |
