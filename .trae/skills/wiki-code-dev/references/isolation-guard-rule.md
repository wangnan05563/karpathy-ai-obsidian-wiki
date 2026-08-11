# 服务端权限隔离守卫规则（CODING-ISOLATION-01 / CODING-ISOLATION-02）

> 复盘来源：权限隔离审查发现，全局 `preHandler` 只「注入 currentUser」而「不拒绝」未认证请求；除 `/api/auth/*` 外的大量写接口（共享配置 / 清理 / 归档 / 隧道 / vault 初始化 / schema / 工具配置 / 各类 ingest）零守卫，导致：
> (1) 游客可越权读写删用户数据、篡改共享服务端密钥；
> (2) 限流 / 审计 IP 若只用 `request.ip`（反向代理下取到代理 IP）或只用 `X-Forwarded-For`（可被客户端伪造），要么误判、要么被绕过。
> 整改引入 auth 感知守卫工厂 `createIsolationGuards(auth?)` 与限流复合键提取函数 `clientIpFromRequest`，并把"服务端 ownership 以受信上下文盖章、绝不信任客户端 body"确立为不变量。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `isolation_guard` 字段读取，禁止在规则文件中硬编码端点路径、守卫名或 IP 提取逻辑。

## CODING-ISOLATION-01：服务端权限隔离（auth 感知守卫 + 服务端 ownerId 盖章）

### 规则

**1. 写端点必须注入 auth 感知守卫**：所有"修改服务端共享状态 / 用户数据"的写端点（`isolation_guard.required_on_write_endpoints` 默认可套 `requireAdmin`），在路由注册时用 `preHandler: guards.requireAdmin`（或 `requireAuth`）声明式注入。守卫由 `createIsolationGuards(config.auth)` 工厂产出，且 **auth 感知**：当 `auth.enabled === false`（单租户 / 本地部署）时一律放行，严格保持既有的"关闭认证 = 全部管理员"部署形态，绝不破坏单租户可用性。

**2. 服务端 ownership 以受信上下文盖章，绝不信任客户端 body**：任何带归属的资源（会话 / 线程记忆 / 归档 / 用户文件），服务端落盘时 `ownerId` 必须由 `request.currentUser.userId`（或受信服务端上下文）写入，**忽略并覆盖客户端请求体里的 `ownerId`**；读取时按当前用户过滤，归属不匹配返回 404（而非 200 携带他人数据或 403 暴露存在性）。

### 适用场景

- Fastify / Express / Koa / NestJS 等带全局 `preHandler`/`middleware` 的后端框架
- 公开 wiki 但含「需登录才能写」的共享状态端点（配置 / 清理 / 归档 / 隧道 / vault / schema）
- 多用户部署（`auth.enabled === true`）下，写端点须强制鉴权
- 单租户部署（`auth.enabled === false`）下，守卫必须直通（保持既有可用性）
- Code Review 涉及 `preHandler` / `requireAuth` / `requireAdmin` / `createIsolationGuards` 注入时
- 排查"游客可越权写 / 篡改共享密钥"类问题时

### 不适用场景

- 完全无认证的公开只读 API（无 token 解析，无写操作）
- 端点级独立鉴权（每个端点单独写 token 解析，不依赖工厂守卫）
- 前端客户端侧隔离（见 CODING-SESSION-ISOLATION / CODING-IDB-REACTIVE-CLONE，归属前端技能）

### 前置检查流程

```
新增/修改写端点:
   ↓
1. 判断该端点是否修改服务端共享状态或用户数据
   ↓
   是 → 路由注册处注入 preHandler: guards.requireAdmin（或 requireAuth）
   ↓
   否（纯只读公开）→ 可保持公开，但确认不泄露敏感字段
   ↓
2. 检查归属资源写入路径
   ↓
   落盘时 ownerId 必须来自 request.currentUser（受信上下文），禁止透传客户端 body.ownerId
   ↓
3. 验证 auth.enabled=false（单租户）时守卫直通（既有权限形态不变）
   ↓
4. 验证 auth.enabled=true 时：无 token → 401；非管理员 → 403/401；管理员 → 200
```

### 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `isolation_guard.enabled` | `true` | 是否启用服务端权限隔离审查（auth 感知守卫 + ownerId 盖章 + 限流复合键） |
| `isolation_guard.admin_permission` | `users` | `requireAdmin` 校验的权限键（管理员角色），`requirePermission(permission, ttl)` 入参 |
| `isolation_guard.pass_through_when_auth_disabled` | `true` | `auth.enabled=false`（单租户）时守卫一律放行，保持"关认证=全管理员"部署形态 |
| `isolation_guard.guard_factory` | `createIsolationGuards` | 守卫工厂函数名（auth 感知：enabled=false 直通） |
| `isolation_guard.required_on_write_endpoints` | `requireAdmin` | 写端点默认注入的守卫（共享配置 / 清理 / 归档 / 隧道等） |
| `isolation_guard.client_ip_composite_key` | `request.ip\|xffFirst` | 限流 / 审计 IP 复合键模板（socket 对端 IP 不可伪造 + XFF 首段），详见 CODING-ISOLATION-02 |

### 检查方式

1. **写端点守卫扫描**：所有修改服务端状态的写端点（`app.post/app.put/app.delete` 中非公开路径）必须带 `preHandler: guards.requireAdmin`（或 `requireAuth`）；缺守卫即报错。
2. **auth 感知直通校验**：守卫工厂必须判断 `auth.enabled`，`false` 时 `return`（放行），不得对单租户部署引入 401。
3. **ownerId 来源校验**：grep 落盘路径，确认 `ownerId` 来自 `request.currentUser.userId` 等受信字段；出现 `request.body.ownerId` 直接赋值落盘即违规。
4. **回归验证**：`auth.enabled=true` 部署下，无 token 调写端点 → 401；非管理员 → 403；管理员 → 200。

### 正确示例

```typescript
// api/src/middleware/auth.ts — auth 感知守卫工厂
export function createIsolationGuards(auth?: IsolationGuardInput): IsolationGuards {
  const enabled = auth?.enabled ?? false;
  const ttlMs = (auth?.permissionCacheTtlSec ?? 300) * 1000;

  const authGuard = async (request, reply) => {
    if (!enabled) return;              // ✅ 单租户：放行
    if (!request.currentUser) {
      reply.code(401).send({ error: '未登录或会话已过期', code: 'UNAUTHORIZED' });
    }
  };
  const adminGuard = async (request, reply) => {
    if (!enabled) return;              // ✅ 单租户：放行
    await requireAdmin(ttlMs)(request, reply);
  };
  return { enabled, requireAuth: authGuard, requireAdmin: adminGuard };
}

// api/src/routes/cleanup.ts — 写端点注入守卫
export function registerCleanupRoute(app, vault, guards: IsolationGuards = createIsolationGuards()) {
  // ✅ 管理员写端点：auth 启用时强制鉴权，关闭时直通
  app.post('/api/cleanup', { preHandler: guards.requireAdmin }, async (request, reply) => { /* ... */ });
}

// 服务端 ownerId 盖章：忽略客户端 body，以受信上下文写入
function persistThread(opts, request) {
  const owner = request.currentUser?.userId ?? null; // ✅ 受信来源
  store.upsert({ ...opts, ownerId: owner });          // ✅ 覆盖任何客户端 body.ownerId
}
```

### 错误示例

```typescript
// ❌ 错误：写端点零守卫，游客可越权改共享密钥
app.put('/api/config/budget', async (request, reply) => {
  await saveBudget(request.body); // 任何人都可调用
});

// ❌ 错误：守卫未 auth 感知，单租户部署下所有写接口变 401
const adminGuard = async (request, reply) => {
  if (!request.currentUser) reply.code(401).send({ error: 'Unauthorized' }); // 缺 enabled 判断
};

// ❌ 错误：信任客户端 body.ownerId，可被伪造改属他人
function persistThread(opts, request) {
  store.upsert({ ...opts, ownerId: request.body.ownerId }); // ❌ 客户端可控归属
}
```

## CODING-ISOLATION-02：限流 / 审计真实客户端 IP 复合键

### 规则

限流桶与审计日志的客户端 IP 提取必须使用 **复合键**：以「不可伪造的 socket 对端 IP（`request.ip`）」为主维度，拼接「`X-Forwarded-For` 首段（`xffFirst`）」为辅助维度，即 `request.ip|xffFirst`。`trust_proxy` 保持 `false`，禁止直接用 `request.ip`（反向代理下取到代理 IP）或只用 `X-Forwarded-For`（客户端可伪造首段）作为限流键——复合键确保即便 XFF 被伪造，socket 对端 IP 仍锁定真实来源，避免限流被绕过或误命中代理 IP。

### 适用场景

- 任何带限流（`@fastify/rate-limit` 或自实现滑动窗口）的端点
- 登录失败 / 鉴权端点等需按客户端 IP 做审计或防爆破的场景
- 反向代理 / SEA / 多机部署（请求经多层转发）

### 不适用场景

- 纯内部服务调用（无外部客户端，IP 单一可信）
- 已用网关层统一限流且应用层不感知客户端 IP 的场景

### 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `isolation_guard.client_ip_composite_key` | `request.ip\|xffFirst` | 限流 / 审计 IP 复合键模板（socket 对端 IP 不可伪造 + XFF 首段） |
| `isolation_guard.trust_proxy` | `false` | 是否信任代理（保持 false 防 XFF 伪造绕过限流） |
| `rate_limit.trust_proxy` | `false` | 限流模块是否信任代理（与 `isolation_guard.trust_proxy` 同源，禁止同时开启） |

### 检查方式

1. **IP 提取函数唯一**：限流 / 审计 IP 须统一从 `clientIpFromRequest(request)`（复合键）读取，禁止散落 `request.ip` 或 `headers['x-forwarded-for']` 直读。
2. **trust_proxy 一致性**：`isolation_guard.trust_proxy` 与 `rate_limit.trust_proxy` 必须同为 `false`（默认），禁止开启以"信任代理 IP"。
3. **复合键格式校验**：确认 key 含 socket 对端 IP（不可伪造维度），而非仅 XFF。

### 正确示例

```typescript
// api/src/auth/auth-rate-limit.ts — 复合键提取
export function clientIpFromRequest(request: FastifyRequest): string {
  const xff = (request.headers['x-forwarded-for'] as string | undefined)?.split(',')[0]?.trim();
  // ✅ socket 对端 IP（不可伪造）为主，XFF 首段为辅，竖线拼接
  return xff ? `${request.ip}|${xff}` : request.ip;
}

// 限流 / 审计统一使用复合键，XFF 伪造也无法绕过（socket IP 锁定真实来源）
const clientIp = clientIpFromRequest(request);
checkAuthRateLimit(clientIp, ...);
```

### 错误示例

```typescript
// ❌ 错误：反向代理下 request.ip 取到代理 IP，限流错命中
const key = request.ip; // 127.0.0.1 / 代理 IP，所有用户共享一个桶

// ❌ 错误：只用 XFF，客户端可伪造首段绕过限流
const key = request.headers['x-forwarded-for'].split(',')[0]; // 客户端可伪造
```

## 与其他规则的关系

- 与 CODING-054（认证端点分类守卫）联动：需鉴权端点禁止误入 `publicPaths` 白名单；本规则负责白名单之外的写端点补守卫。
- 与 CODING-SESSION-ISOLATION（前端会话隔离）/ CODING-BYOK（多用户密钥代理）同源：都是"多用户数据必须以身份维度隔离、不可信客户端可控归属"这一判断逻辑的服务端侧落地。
- 与 CODING-IDB-REACTIVE-CLONE 互补：前者管服务端归属盖章，后者管前端客户端持久化的 reactive 代理剥离；跨端归属隔离两端各有编号。
- 与 BR-063（限流韧性）/ BR-ISOLATION-03 同源：复合键防 XFF 伪造，与"trustProxy 默认 false"一致。

## 适配新项目

- 适配 Express：`guard_factory` 改为 `use` 中间件封装，`pass_through_when_auth_disabled` 同样需判断 `auth.enabled`。
- 适配 Koa：`guard_factory` 改为 `app.use` 风格，`ctx.state.user` 替代 `request.currentUser`。
- 适配 NestJS：用 `@Roles()` + `AuthGuard` 装饰器，守卫内仍需判断 `auth.enabled` 直通单租户。
- 适配无认证应用：`isolation_guard.enabled` 设为 `false`，守卫全放行（与单租户直通等价）。
