# Rule Catalog — 认证/异步请求超时兜底 (CODING-AUTH-REQUEST-TIMEOUT)

通用前端编码规范：所有认证与关键异步请求（登录、会话校验、BYOK 问答等）必须携带 `AbortController` + 可配置超时，禁止无超时上限的 `await` 悬挂。请求超时须给出明确文案（如「登录超时，请检查网络或服务器后重试」）并允许重试，绝不能让按钮永久处于「登录中」灰显状态。本规则是前端审查条目 `wiki-frontend-code-review` FR-082 的上位规范。

> 复盘来源：`auth` store 的登录 `fetch` 未包裹 `AbortController` 与超时，网络慢/服务端无响应时 `await` 永久悬挂，登录按钮灰显且一直显示「登录中」卡死。修正：所有认证请求统一经带超时的封装（如 `fetchWithTimeout` / `AbortSignal.timeout(ms)`），超时即 reject 并复位 loading。

## Scope

- Covers: 登录、会话校验、任何"用户点击后进入等待态"的关键异步请求（含 BYOK 问答的 SSE 前置鉴权）。
- Does NOT cover: 纯本地同步计算；明确标注为 fire-and-forget 的非阻塞心跳探针（仍建议带超时）。

## Rules

### CODING-AUTH-REQUEST-TIMEOUT-1: 关键异步请求必须带超时

IsUrgent: True（严重）
Category: 异步可靠性 / 前端

#### Description

认证与关键请求必须设超时上限（来自配置，默认 30s），经 `AbortController` / `AbortSignal.timeout(ms)` 包裹。超时须 reject 而非悬挂，使上层 `catch` 能复位 UI 状态。禁止裸 `await fetch(url)` 无超时。

#### Suggested Fix

```ts
// ✅ 带超时的认证请求封装
export async function loginWithTimeout(creds: Creds, timeoutMs = AUTH_TIMEOUT_MS): Promise<Session> {
  const ctrl = new AbortController()
  const t = setTimeout(() => ctrl.abort(), timeoutMs)
  try {
    const res = await fetch('/api/auth/login', { method: 'POST', body: JSON.stringify(creds), signal: ctrl.signal })
    if (!res.ok) throw new Error(`login failed ${res.status}`)
    return await res.json()
  } finally {
    clearTimeout(t)
  }
}
```

### CODING-AUTH-REQUEST-TIMEOUT-2: 超时文案必须明确且可重试

IsUrgent: False
Category: 异步可靠性 / 前端 UX

#### Description

超时错误须向用户展示可操作文案（检查网络/服务器/重试），并解除按钮禁用态，允许用户再次点击。禁止超时后按钮仍灰显、无限「登录中」。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `auth_request_timeout.enabled` | `true` | 启用认证/异步请求超时兜底审查 |
| `auth_request_timeout.timeout_ms` | `30000` | 关键请求超时阈值（从配置读取，禁止硬编码字面量） |
| `auth_request_timeout.margin_multiplier` | `1.5` | 前端阈值相对后端超时的余量倍数（前端 > 后端，避免提前断） |
| `auth_request_timeout.required_pattern` | `AbortController|AbortSignal.timeout` | 认证/关键请求须出现的超时包裹模式 |
| `auth_request_timeout.severity` | `critical` | 无超时悬挂导致按钮卡死的违规级别 |
