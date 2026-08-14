# Rule Catalog — 前端受保护接口必须经带鉴权封装调用 (CODING-AUTH-REQUEST-FETCH)

通用前端编码规范：所有**受保护 API 端点**（后端挂 `requireAuth` 守卫的接口，如 `GET /api/config`、`GET /api/ai/config`）必须统一经**带鉴权封装的共享 HTTP 客户端**（本项目为 `frontend/src/utils/apiBase.ts` 的 `apiFetch`）调用；该封装从 `localStorage` 读取 Bearer token 并注入 `Authorization` 头。禁止在业务代码里用**裸 `fetch` 不带 token** 直接请求受保护端点，否则后端 `requireAuth` 返 `401`，导致 AI 伙伴选项消失、`加载配置失败：HTTP 401` 等静默失效。本规则是前端审查条目 `wiki-frontend-code-review` FR-084 与后端审查条目 `wiki-backend-code-review` BR-094 的上位规范。

> 复盘来源：后端在 `config.auth.enabled: true` 启用后，对 `GET /api/config`、`GET /api/ai/config` 挂 `requireAuth` 守卫要求 Bearer token；但前端 18 处裸 `fetch` 未带 token（且不依赖 Pinia，独立封装），统一请求这俩端点时拿到 `401`——AI 伙伴选项整体消失 + 控制台「加载配置失败：HTTP 401」。修复：新增 `apiFetch`（读 `localStorage` token，不依赖 Pinia），全站裸 `fetch` → `apiFetch` 迁移。核心教训：**受保护接口与"带 token 的封装"是一对契约，缺任何一端都会 401**。

## Scope

- Covers: 所有请求**受保护端点**（后端 `requireAuth` 守卫覆盖、须 Bearer token 的接口）的前端调用；以及"给原先公开端点加 `requireAuth`"这类**破坏性变更**的前后端契约一致性。
- Does NOT cover: 显式公开的端点（`publicPaths` 白名单，如 `/api/auth/login`、`/health`）；纯静态资源；已在 `apiBase.ts` 内部统一注入 token 的 `apiFetch` 自身实现。

## Rules

### CODING-AUTH-REQUEST-FETCH-1: 受保护端点必须走带鉴权封装

IsUrgent: True（严重）
Category: 前端 / 认证契约

#### Description

凡请求后端 `requireAuth` 端点（含 `GET /api/config`、`GET /api/ai/config` 等 bootstrap 配置接口），必须经由共享的带鉴权 HTTP 客户端（`apiFetch`）调用，禁止在 `.vue` / `.ts` 业务代码里裸 `fetch(url)` / `fetch(url, { method })` 不带 `Authorization` 头。裸 fetch 命中 `requireAuth` 即 `401`，且失败通常静默（仅控制台报错），比显式崩溃更隐蔽。

#### Suggested Fix

```ts
// ✅ 统一经 apiFetch（内部读 localStorage token 注入 Authorization）
import { apiFetch } from '@/utils/apiBase'
const cfg = await apiFetch('/api/config')            // 自动带 Bearer token

// ❌ 裸 fetch 调受保护端点（缺 token → 401 静默失效）
const cfg = await fetch('/api/config').then(r => r.json())
```

### CODING-AUTH-REQUEST-FETCH-2: 鉴权封装须从非 Pinia 源读取 token

IsUrgent: True（严重）
Category: 前端 / 启动期依赖

#### Description

带鉴权封装读取 token 的来源必须是 **`localStorage` 等模块级可用存储**，而非 Pinia store / `auth` store。原因：受保护端点（如 `/api/config`）常在**应用 bootstrap 期**、Pinia 与 auth store 尚未初始化完成前就被请求；若封装依赖 Pinia，会陷入"取 token 前 store 未就绪"的鸡生蛋问题。封装须自包含、可独立调用。

#### Suggested Fix

```ts
// ✅ apiBase.ts 内部直接读 localStorage，不 import 任何 Pinia store
export async function apiFetch(path: string, init: RequestInit = {}) {
  const token = localStorage.getItem('authToken') ?? ''
  const headers = new Headers(init.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  return fetch(path, { ...init, headers })
}
```

### CODING-AUTH-REQUEST-FETCH-3: 给公开端点加 requireAuth 是破坏性变更，须审计全部前端调用方

IsUrgent: True（严重）
Category: 前后端契约 / 变更管控

#### Description

后端把原先**公开**的端点改为挂 `requireAuth`（如 `/api/config` 从 public 变 protected），是**破坏性变更**：它要求**所有前端调用方**都已使用带鉴权封装。新增/收紧 `requireAuth` 时，必须：(1) 列出该端点全部前端调用点；(2) 确认每处都经 `apiFetch`（或等价带 token 封装）；(3) 在 PR 描述中标注"端点鉴权升级 + 调用方审计"。缺此步骤即会复现 401 静默失效。

#### Suggested Fix

```text
变更清单示例：
- 后端：GET /api/config 挂 requireAuth（原为 public）
- 前端调用方审计：config store / App.vue bootstrap / Settings 加载 → 全部改 apiFetch
- 验证：缺 token 请求 → 期望 401；带 token → 期望 200；全站无裸 fetch 直连该端点
```

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `auth_request_fetch.enabled` | `true` | 启用"受保护端点须带鉴权封装"审查 |
| `auth_request_fetch.protected_endpoint_patterns` | `/api/config`,`/api/ai/config` | 受保护端点路径片段（命中裸 fetch 即违规），来自配置不硬编码 |
| `auth_request_fetch.wrapper_symbol` | `apiFetch` | 带鉴权封装函数/符号名（存在性守卫，required_patterns 用） |
| `auth_request_fetch.token_source` | `localStorage` | 封装读取 token 的源（须非 Pinia，避免 bootstrap 期依赖） |
| `auth_request_fetch.severity` | `critical` | 裸 fetch 调受保护端点导致 401 静默失效的违规级别 |
| `auth_request_fetch.breaking_change_audit` | `true` | 给公开端点加 requireAuth 时，是否强制调用方审计（BR-094 配套） |
