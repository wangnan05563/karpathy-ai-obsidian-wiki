# 服务端权限隔离审查规则（BR-ISOLATION）

> 复盘来源：权限隔离审查发现，全局 `preHandler` 只「注入 currentUser」而「不拒绝」未认证请求；除 `/api/auth/*` 外的大量写接口（共享配置 / 清理 / 归档 / 隧道 / vault 初始化 / schema / 工具配置 / 各类 ingest）零守卫，导致游客可越权读写删用户数据、篡改共享服务端密钥。同时限流 / 审计 IP 若只用 `request.ip`（反向代理下取到代理 IP）或只用 `X-Forwarded-For`（客户端可伪造首段），要么误判、要么被绕过。整改引入 auth 感知守卫工厂 `createIsolationGuards(auth?)` 与限流复合键提取函数 `clientIpFromRequest`，并确立"服务端 ownership 以受信上下文盖章、绝不信任客户端 body"为不变量。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"服务端权限隔离审查参数（server_side_isolation）"章节读取，禁止在本规则文件硬编码阈值、端点路径或守卫名。

## Trigger Keywords

preHandler, requireAdmin, requireAuth, createIsolationGuards, ownerId, owner_id, isPublicPath, X-Forwarded-For, clientIpFromRequest, request.ip, 401, 403, admin, RBAC, auth.enabled, trustProxy, 限流复合键, 服务端盖章

## Rules

### BR-ISOLATION-01：写端点必须注入 auth 感知守卫（单租户直通）

- **Severity**: critical
- **Description**: 所有"修改服务端共享状态 / 用户数据"的写端点（`app.post/app.put/app.delete` 中非公开路径）必须用 `preHandler: guards.requireAdmin`（或 `requireAuth`）声明式注入守卫。守卫由 `createIsolationGuards(config.auth)` 工厂产出且 **auth 感知**：当 `auth.enabled === false`（单租户 / 本地部署）时一律放行，严格保持既有的"关闭认证 = 全部管理员"部署形态。**评审时确认**：① 写端点缺 `preHandler` 守卫即违规；② 守卫工厂必须判断 `auth.enabled`，`false` 时 `return`（放行），不得对单租户部署引入 401（破坏既有可用性）。
- **Suggested fix**:

```typescript
// 错误：写端点零守卫，游客可越权改共享密钥
app.put('/api/config/budget', async (request, reply) => {
  await saveBudget(request.body); // ❌ 任何人都可调用
});

// 错误：守卫未 auth 感知，单租户部署下所有写接口变 401
const adminGuard = async (request, reply) => {
  if (!request.currentUser) reply.code(401).send({ error: 'Unauthorized' }); // ❌ 缺 enabled 判断
};

// 正确：写端点注入 auth 感知守卫，单租户直通、多用户强制鉴权
export function registerCleanupRoute(app, vault, guards: IsolationGuards = createIsolationGuards()) {
  app.post('/api/cleanup', { preHandler: guards.requireAdmin }, async (request, reply) => { /* ... */ });
}
```

### BR-ISOLATION-02：服务端 ownerId 以受信上下文盖章，不信任客户端 body

- **Severity**: critical
- **Description**: 任何带归属的资源（会话 / 线程记忆 / 归档 / 用户文件），服务端落盘时 `ownerId` 必须由 `request.currentUser.userId`（或受信服务端上下文）写入，**忽略并覆盖客户端请求体里的 `ownerId`**；读取时按当前用户过滤，归属不匹配返回 404（而非 200 携带他人数据或 403 暴露存在性）。**评审时确认**：grep 落盘路径，凡出现 `request.body.ownerId` 直接赋值落盘即违规；缺归属过滤的列表接口会被越权枚举。
- **Suggested fix**:

```typescript
// 错误：信任客户端 body.ownerId，可被伪造改属他人
function persistThread(opts, request) {
  store.upsert({ ...opts, ownerId: request.body.ownerId }); // ❌ 客户端可控归属
}

// 正确：服务端以受信上下文盖章，覆盖任何客户端 body.ownerId
function persistThread(opts, request) {
  const owner = request.currentUser?.userId ?? null; // ✅ 受信来源
  store.upsert({ ...opts, ownerId: owner });          // ✅ 覆盖客户端传入
}
// 读取时按 owner 过滤，不匹配返回 404
const meta = store.getThread(id);
if (meta?.ownerId && meta.ownerId !== request.currentUser?.userId) {
  return reply.code(404).send({ error: 'Not Found' });
}
```

### BR-ISOLATION-03：限流 / 审计真实客户端 IP 复合键（防 XFF 伪造）

- **Severity**: critical
- **Description**: 限流桶与审计日志的客户端 IP 提取必须使用 **复合键**：以「不可伪造的 socket 对端 IP（`request.ip`）」为主维度，拼接「`X-Forwarded-For` 首段（`xffFirst`）」为辅助维度，即 `request.ip|xffFirst`。`trust_proxy` 保持 `false`，禁止直接用 `request.ip`（反向代理下取到代理 IP，限流错命中）或只用 `X-Forwarded-For`（客户端可伪造首段，限流被绕过）。复合键确保即便 XFF 被伪造，socket 对端 IP 仍锁定真实来源。**评审时确认**：限流 / 审计 IP 统一从 `clientIpFromRequest(request)` 读取；`isolation_guard.trust_proxy` 与 `rate_limit.trust_proxy` 同为 `false`（默认），禁止开启。
- **Suggested fix**:

```typescript
// 错误：反向代理下 request.ip 取到代理 IP，限流错命中
const key = request.ip; // 127.0.0.1 / 代理 IP，所有用户共享一个桶

// 错误：只用 XFF，客户端可伪造首段绕过限流
const key = request.headers['x-forwarded-for'].split(',')[0]; // ❌ 客户端可伪造

// 正确：复合键（socket 对端 IP 不可伪造 + XFF 首段），XFF 伪造也无法绕过
export function clientIpFromRequest(request: FastifyRequest): string {
  const xff = (request.headers['x-forwarded-for'] as string | undefined)?.split(',')[0]?.trim();
  return xff ? `${request.ip}|${xff}` : request.ip;
}
const clientIp = clientIpFromRequest(request);
checkAuthRateLimit(clientIp, ...);
```

## 与其他规则的关系

- 与 BR-048/049（认证端点分类）联动：需鉴权端点禁止误入 `publicPaths` 白名单；本规则负责白名单之外的写端点补守卫。
- 与 BR-063（限流韧性）同源：`trustProxy` 默认 `false`、限流键防伪造；本规则将其收敛为"复合键"单一提取函数。
- 与 BR-072（BYOK 多用户密钥代理）/ BR-088（审查范围判定）互补：跨端归属隔离前后端各有编号，服务端侧归属盖章属本规则，前端客户端持久化隔离属 FR-081/CODING-IDB-REACTIVE-CLONE。
