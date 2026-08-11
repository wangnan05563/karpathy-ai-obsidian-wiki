# Rule Catalog — 路由 return 完整性 (BR-089)

后端审查条目，对应通用编码规范 `CODING-ROUTE-RETURN-COMPLETENESS`（wiki-code-dev references/route-return-completeness-rule.md）。Fastify 路由处理函数中，**每个分支都必须 `return` / `reply`**，禁止任何执行路径"漏 return"后落到函数末尾。Fastify 在 handler 返回 `undefined` 时会隐式调用 `reply.send()`，若此前已 `res.send` / 已 `return reply.xxx` 则触发 `ERR_STREAM_WRITE_AFTER_END` 双发响应，或静默挂起使前端收到空响应 / 超时。本规则扩展 BR-ESM-04（端点可达性）。

> 复盘来源：`auth.ts` 登录路由在某分支（如参数校验失败）走完逻辑却漏写 `return`，执行流落到函数末尾，Fastify 隐式再发一次响应，与已有响应冲突导致前端登录请求异常/超时。修正：每个 `if/else` 分支与提前退出点都显式 `return`，并对 `async` handler 统一收口。

## Scope

- Covers: 所有 Fastify 路由 `handler`（`async (req, reply) => {...}`），尤其含多分支校验 / 提前 `return reply.send()` 的函数。
- Does NOT cover: 纯中间件 `preHandler`（无响应职责）；已通过 `reply` 对象统一收口且 `throw` 由 `setErrorHandler` 接管的情况。

## Rules

### BR-089-1: 每个分支都必须 return/reply

Category: 后端 / 路由正确性
Severity: critical

#### Description

路由 handler 内每个 `if/else if/else` 分支、每个提前退出点（`if (!ok) return reply.code(400)...`）都必须显式 `return`（或 `throw` 交错误处理器）。不得有"执行完逻辑却无 return"的分支落入函数末尾。

#### Suggested Fix

```ts
// ✅ 每个分支显式 return
fastify.post('/api/auth/login', async (req, reply) => {
  const { user, pass } = req.body ?? {}
  if (!user || !pass) {
    return reply.code(400).send({ error: 'missing credential' }) // 显式 return
  }
  const session = await authenticate(user, pass)
  if (!session) {
    return reply.code(401).send({ error: 'invalid credential' }) // 显式 return
  }
  return reply.send({ token: session.token }) // 主路径 return
})
```

### BR-089-2: async handler 禁止隐式 undefined 落底

Category: 后端 / 路由正确性
Severity: critical

#### Description

`async` handler 若任一分支未 `return`，Promise 解析为 `undefined`，Fastify 会隐式 `reply.send()`，与已有响应冲突。审查须确认无"漏 return"分支；可借助 `reply` 收口或显式 `return reply.send()`。

## Configuration Parameters

> 全部参数从 [config/review-config.md](../config/review-config.md) 的"路由 return 完整性审查参数（BR-089）"节读取，本规则文件不硬编码任何值。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `route_return_completeness.enabled` | `true` | 启用路由 return 完整性审查 |
| `route_return_completeness.reply_api` | `reply.send,reply.code,reply.status` | 视为已响应的 reply 调用 |
| `route_return_completeness.severity` | `critical` | 漏 return 导致双发响应 / 前端超时的违规级别 |
