# Rule Catalog — Auth/Async Request Timeout Fallback (Frontend)

前端「认证/异步请求超时兜底」审查规则：登录 / 会话校验 / 任何"用户点击后进入等待态"的关键异步请求必须携带 `AbortController` + 可配置超时，禁止无超时上限的 `await` 悬挂。超时须给出明确可重试文案并解除按钮禁用态，绝不能让按钮永久「登录中」灰显。所有参数从 `config/review-config.md` 读取，禁止硬编码。

> 复盘来源：初次登录时 `auth` store 的登录 `fetch` 未包裹 `AbortController` 与超时，网络慢 / 服务端无响应时 `await` 永久悬挂，登录按钮灰显且一直显示「登录中」，用户只能刷新页面。修正：所有认证请求统一经带超时的封装（`fetchWithTimeout` / `AbortSignal.timeout(ms)`），超时即 reject 并复位 loading；阈值来自配置（默认 `auth_request_timeout_frontend.timeout_ms`），前端阈值须大于后端（margin 余量），避免提前断开。

## Scope

- Covers: 登录、会话校验、任何"用户点击后进入等待态"的关键异步请求（含 BYOK 问答的 SSE 前置鉴权 / 保存配置 / 提交）。
- Does NOT cover：纯本地同步计算；明确标注为 fire-and-forget 的非阻塞心跳探针（仍建议带超时）。

## Rules

### FR-082-1: 关键异步请求必须带超时

IsUrgent: True
Category: Auth Request Timeout

#### Description

认证与关键请求必须设超时上限（来自配置，默认 30s），经 `AbortController` / `AbortSignal.timeout(ms)` 包裹。超时须 reject 而非悬挂，使上层 `catch` 能复位 UI 状态。禁止裸 `await fetch(url)` 无超时（FR-082-1，Critical）。

```typescript
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

### FR-082-2: 超时文案必须明确且可重试

IsUrgent: False
Category: Auth Request Timeout

#### Description

超时错误须向用户展示可操作文案（如「登录超时，请检查网络或服务器后重试」）并解除按钮禁用态，允许用户再次点击。禁止超时后按钮仍灰显、无限「登录中」（FR-082-2，建议级）。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `auth_request_timeout_frontend.enabled` | `true` | 启用本组规则（FR-082） |
| `auth_request_timeout_frontend.timeout_ms` | `30000` | 关键请求（登录/会话校验）超时阈值，从配置读取，禁止硬编码字面量 |
| `auth_request_timeout_frontend.margin_multiplier` | `1.5` | 前端阈值相对后端超时的余量倍数（前端 > 后端，避免提前断） |
| `auth_request_timeout_frontend.required_pattern` | `AbortController\|AbortSignal.timeout` | 认证/关键请求须出现的超时包裹模式 |
| `auth_request_timeout_frontend.severity_no_timeout` | `critical` | FR-082-1 无超时悬挂导致按钮卡死违规级别 |
| `auth_request_timeout_frontend.severity_no_retry` | `suggestion` | FR-082-2 超时无明确可重试文案违规级别 |
