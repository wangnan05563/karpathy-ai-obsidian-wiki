# Rule Catalog — 受保护接口契约 (BR-094)

后端审查条目，对应通用编码规范 `CODING-AUTH-REQUEST-FETCH`（wiki-code-dev references/auth-request-fetch-rule.md）。后端 `requireAuth` 守卫覆盖的端点（如 `GET /api/config`、`GET /api/ai/config`）必须**显式登记其鉴权契约**，使"哪些端点要 Bearer token"可被前端调用方与测试静态审计；且把**原先公开的端点收紧为 `requireAuth`** 属于**破坏性变更**，必须审计全部前端调用方、确认已迁移到带鉴权封装（`apiFetch`），否则会复现 401 静默失效。

> 复盘来源：后端 `config.auth.enabled: true` 启用后，对 `GET /api/config`、`GET /api/ai/config` 挂 `requireAuth` 要求 Bearer token；但前端 18 处裸 `fetch` 未带 token（且不依赖 Pinia，是独立封装），统一请求这俩端点时拿到 `401`——AI 伙伴选项整体消失 + 控制台「加载配置失败：HTTP 401」。根因是"端点鉴权要求"未在契约层声明、且收紧鉴权时未审计前端调用方。对应前端 FR-084（受保护接口必须带鉴权封装调用）/ wiki-auto-testing `frontend_review_static_check` 的 `auth_fetch_wrapped` 组。

## Scope

- Covers: 后端 `requireAuth` 守卫覆盖的路由的鉴权契约声明；"公开端点 → 受保护端点"的收紧变更及其前端调用方审计；bootstrap 期被前端请求的受保护端点（`/api/config`、`/api/ai/config`）的 token 注入可行性。
- Does NOT cover: 显式公开端点（`publicPaths` 白名单，如 `/api/auth/login`、`/health`）的鉴权豁免本身（见 BR-048-1）；鉴权守卫对单租户 `auth.enabled=false` 直通的形态（见 BR-ISOLATION-01）；`apiFetch` 前端实现细节（见前端 FR-084）。

## Rules

### BR-094-1: 受保护端点须显式登记鉴权契约

Category: 后端 / 认证契约 / 可审计性
Severity: critical

#### Description

所有挂 `requireAuth`（或 `requireAdmin`）守卫的路由，必须在**权威登记处**声明其鉴权要求（例如在路由注册处统一登记、或维护一份"端点 → 是否需 token"的契约清单），使前端调用方、测试与审查可静态判断"哪些端点要 Bearer token"。禁止仅在守卫里静默加 `requireAuth` 而不登记——这种"暗改"会让前端裸 `fetch` 调用方在毫无提示下拿到 401 并静默失效（BR-094-1，Critical）。

#### Suggested Fix

```typescript
// ✅ 路由注册处显式登记鉴权要求，契约可审计
app.get('/api/config', { preHandler: guards.requireAuth }, getConfigHandler)

// ❌ 暗改：仅在守卫逻辑里对 /api/config 加 requireAuth，但路由表/契约清单未登记
//   → 前端 18 处裸 fetch 调用方无提示，全部 401 静默失效
```

### BR-094-2: 收紧端点鉴权是破坏性变更，须审计全部前端调用方

Category: 后端 / 认证契约 / 破坏性变更
Severity: major

#### Description

把**原先公开的端点**改为挂 `requireAuth`（如 `/api/config` 从 public 变 protected），是**破坏性变更**：它要求**所有前端调用方**都已使用带鉴权封装（`apiFetch`，内部注入 `Authorization`）。新增 / 收紧 `requireAuth` 时，PR 描述须标注"端点鉴权升级 + 调用方审计"，并确认每处前端调用方都已迁移（BR-094-2，Major）。缺此步骤即复现 401 静默失效（AI 伙伴选项消失 / 「加载配置失败：HTTP 401」）。前端对应规则 FR-084-3。

#### Suggested Fix

```markdown
# PR 描述须标注（收紧鉴权时）
> 端点鉴权升级：/api/config、/api/ai/config 由 public 改为 requireAuth。
> 调用方审计：前端 18 处裸 fetch 已全部迁移到 apiFetch（见 FR-084-3）。
```

## Configuration Parameters

> 全部参数从 [config/review-config.md](../config/review-config.md) 的"受保护接口契约审查参数（BR-094）"节读取，本规则文件不硬编码任何值。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `auth_endpoint_contract.enabled` | `true` | 启用受保护接口契约审查 |
| `auth_endpoint_contract.contract_source` | `routes/*.ts 路由注册守卫` | "端点 → 鉴权要求"权威登记处的位置（须可被静态审计） |
| `auth_endpoint_contract.bootstrap_endpoints` | `/api/config,/api/ai/config` | 应用 bootstrap 期被前端请求的受保护端点（须确保前端封装在 Pinia/auth store 初始化前即可注入 token） |
| `auth_endpoint_contract.wrapper_symbol` | `apiFetch` | 前端须使用的带鉴权封装符号名（收紧鉴权时调用方须已迁移至此） |
| `auth_endpoint_contract.severity_undeclared` | `critical` | BR-094-1 受保护端点未在契约登记、调用方不可审计的违规级别 |
| `auth_endpoint_contract.severity_breaking_audit` | `major` | BR-094-2 收紧 requireAuth 未审计前端调用方 / 未标注破坏性变更的违规级别 |
