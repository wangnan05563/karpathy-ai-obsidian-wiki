# Rule Catalog — 受保护接口必须带鉴权封装调用 (Frontend, FR-084)

前端「受保护接口必须带鉴权封装调用」审查规则：所有请求**后端 `requireAuth` 受保护端点**（如 `GET /api/config`、`GET /api/ai/config`）必须统一经**带鉴权封装的共享 HTTP 客户端**（本项目 `frontend/src/utils/apiBase.ts` 的 `apiFetch`）调用，禁止在业务代码里用**裸 `fetch` 不带 token** 直接请求。裸 fetch 命中 `requireAuth` 即 `401`，且失败通常静默（仅控制台），导致 AI 伙伴选项消失、`加载配置失败：HTTP 401` 等隐蔽失效。所有参数从 `config/review-config.md` 读取，禁止硬编码。

> 复盘来源：后端 `config.auth.enabled: true` 启用后对 `GET /api/config`、`GET /api/ai/config` 挂 `requireAuth` 要求 Bearer token；但前端 18 处裸 `fetch` 未带 token（且不依赖 Pinia，是独立封装），统一请求这俩端点时拿到 `401`——AI 伙伴选项整体消失 + 控制台「加载配置失败：HTTP 401」。修复：新增 `apiFetch`（读 `localStorage` token，不依赖 Pinia），全站裸 `fetch` → `apiFetch` 迁移。对应 wiki-code-dev CODING-AUTH-REQUEST-FETCH / 后端 BR-094。

## Scope

- Covers: 所有请求**受保护端点**（后端 `requireAuth` 守卫覆盖、须 Bearer token 的接口）的前端调用；"给原先公开端点加 `requireAuth`"这类破坏性变更的前端调用方审计。
- Does NOT cover: 显式公开端点（`publicPaths` 白名单，如 `/api/auth/login`、`/health`）；纯静态资源；`apiFetch` 自身实现（已在 `apiBase.ts` 统一注入 token）。

## Rules

### FR-084-1: 受保护端点必须走带鉴权封装

IsUrgent: True
Category: Auth Request Fetch Wrapping

#### Description

凡请求后端 `requireAuth` 端点（含 `GET /api/config`、`GET /api/ai/config` 等 bootstrap 配置接口），必须经由共享的带鉴权 HTTP 客户端（`apiFetch`）调用，禁止在 `.vue` / `.ts` 业务代码里裸 `fetch(url)` / `fetch(url, { method })` 不带 `Authorization` 头。命中 `protected_endpoint_patterns` 且未走 `wrapper_symbol` 即违规（FR-084-1，Critical）。裸 fetch 命中 `requireAuth` 即 `401`，且失败静默，比显式崩溃更隐蔽。

```typescript
// ✅ 统一经 apiFetch（内部读 localStorage token 注入 Authorization）
import { apiFetch } from '@/utils/apiBase'
const cfg = await apiFetch('/api/config')

// ❌ 裸 fetch 调受保护端点（缺 token → 401 静默失效）
const cfg = await fetch('/api/config').then(r => r.json())
```

### FR-084-2: 鉴权封装须从非 Pinia 源读取 token

IsUrgent: True
Category: Auth Request Fetch Wrapping

#### Description

带鉴权封装读取 token 的来源必须是 **`localStorage` 等模块级可用存储**，而非 Pinia store / `auth` store。受保护端点（如 `/api/config`）常在**应用 bootstrap 期**、Pinia 与 auth store 尚未初始化前就被请求；若封装依赖 Pinia，会陷入"取 token 前 store 未就绪"的鸡生蛋问题（FR-084-2，Critical）。封装须自包含、可独立调用。

### FR-084-3: 给公开端点加 requireAuth 是破坏性变更，须审计调用方

IsUrgent: False
Category: Auth Request Fetch Wrapping

#### Description

后端把原先**公开**的端点改为挂 `requireAuth`（如 `/api/config` 从 public 变 protected），是**破坏性变更**：它要求**所有前端调用方**都已使用带鉴权封装。新增/收紧 `requireAuth` 时，PR 描述须标注"端点鉴权升级 + 调用方审计"，并确认每处都经 `apiFetch`（FR-084-3，Major）。缺此步骤即复现 401 静默失效。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `auth_request_fetch_frontend.enabled` | `true` | 启用本组规则（FR-084） |
| `auth_request_fetch_frontend.protected_endpoint_patterns` | `/api/config`,`/api/ai/config` | 受保护端点路径片段（命中裸 fetch 即违规），来自配置不硬编码 |
| `auth_request_fetch_frontend.wrapper_symbol` | `apiFetch` | 带鉴权封装函数/符号名（存在性守卫 + 替换目标） |
| `auth_request_fetch_frontend.token_source` | `localStorage` | 封装读取 token 的源（须非 Pinia，避免 bootstrap 期依赖） |
| `auth_request_fetch_frontend.severity_missing_wrap` | `critical` | FR-084-1 裸 fetch 调受保护端点导致 401 静默失效违规级别 |
| `auth_request_fetch_frontend.severity_token_source` | `critical` | FR-084-2 封装依赖 Pinia 致 bootstrap 期取 token 失败违规级别 |
| `auth_request_fetch_frontend.severity_breaking_audit` | `major` | FR-084-3 收紧 requireAuth 未审计调用方违规级别 |
