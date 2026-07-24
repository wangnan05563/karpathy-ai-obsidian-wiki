# 认证端点分类审查规则（BR-048~049）

> 复盘来源：Skill 导入模块开发中 `/api/auth/me` 被误放入 `publicPaths` 白名单，导致全局 preHandler 跳过 token 解析、`currentUser` 永远为 null，authGuard 必然返回 401（CODING-054）。看似"公开"端点放入白名单，实际反而让认证失效，是反直觉陷阱。
> 所有可变参数（端点路径、中间件 hook 名、跳过机制名）从 [config/review-config.md](../config/review-config.md) 的"认证端点分类审查参数（auth_endpoint_classification）"章节读取，禁止在本规则文件硬编码具体端点路径或中间件名称。

## Trigger Keywords

publicPaths, preHandler, authGuard, /api/auth/me, currentUser, 401, token 解析, setupAuthMiddleware, isPublicPath, /api/auth/login, /health, /api/auth/logout, 认证中间件, 白名单

## Rules

### BR-048-1：publicPaths 白名单只能包含完全公开端点

- **Severity**: critical
- **Description**: `publicPaths`（白名单）中的路径会让全局认证中间件 hook（`auth_endpoint_classification.middleware_hook`，默认 `preHandler`）跳过 token 解析（`auth_endpoint_classification.skip_mechanism`，默认 `isPublicPath`）。因此白名单只能包含完全公开端点（如 `auth_endpoint_classification.public_paths_whitelist`，默认 `/api/auth/login,/health`），需鉴权端点（如 `auth_endpoint_classification.auth_required_endpoints`，默认 `/api/auth/me,/api/auth/logout`）禁止放入。误放入白名单会导致 token 解析被跳过、`currentUser` 永远为 null、authGuard 必然返回 401——这是反直觉陷阱，"公开"反而让认证失效。
- **Suggested fix**:

```typescript
// 错误：/api/auth/me 误放入 publicPaths，preHandler 跳过 token 解析
setupAuthMiddleware(app, {
  publicPaths: ['/api/auth/login', '/health', '/api/auth/me'], // ❌ me 是需鉴权端点
});
// 结果：request.currentUser 永远为 null，authGuard 必然返回 401

// 正确：publicPaths 只保留完全公开端点（路径从 config 读取）
// config: auth_endpoint_classification.public_paths_whitelist = '/api/auth/login,/health'
setupAuthMiddleware(app, {
  publicPaths: ['/api/auth/login', '/health'], // ✅ me 走正常 token 解析流程
});
```

### BR-048-2：publicPaths 反直觉陷阱——"公开"实际导致认证失效

- **Severity**: critical
- **Description**: `publicPaths` 的语义是反直觉的：开发者往往以为"把端点放入 publicPaths = 让所有人都能访问"，但实际语义是"跳过 token 解析 = `currentUser` 永远为 null"。对于 `/api/auth/me` 这种"获取当前用户信息"的端点，跳过解析后 authGuard 因 `currentUser` 为 null 必然返回 401，即使携带有效 token 也无法通过——表现为"明明登录了却 401"，问题难以定位。评审时必须显式确认 `publicPaths` 中每个路径都是"无登录态也能返回有意义响应"的端点（如 login/health），而非"需要登录但希望放行"的端点。
- **Suggested fix**:

```typescript
// 错误：误以为 publicPaths = "放行已登录用户"
// 实际语义：publicPaths = "跳过 token 解析，currentUser 永远 null"
setupAuthMiddleware(app, {
  publicPaths: ['/api/auth/login', '/health', '/api/auth/me'], // ❌ 反直觉陷阱
});

// 正确：理解 publicPaths 真实语义，只放完全公开端点
// /api/auth/me 必须走正常 token 解析，未登录时由 authGuard 返回 401
setupAuthMiddleware(app, {
  publicPaths: ['/api/auth/login', '/health'], // ✅ 从 config 读取
});
```

### BR-049-1：需鉴权端点必须走正常 token 解析流程

- **Severity**: critical
- **Description**: `/api/auth/me` 等"获取当前用户信息"端点（见 `auth_endpoint_classification.auth_required_endpoints`）必须走正常 token 解析流程——preHandler 解析 token 后写入 `request.currentUser`，handler 内通过 `request.currentUser` 读取用户信息。未登录（无 token 或 token 无效）时由 authGuard 返回 401，**而非**通过 `publicPaths` 跳过解析后返回 null user。评审时确认 `auth_required_endpoints` 列表中的端点均不在 `publicPaths` 中，且 handler 内访问 `request.currentUser` 时有非空守卫。
- **Suggested fix**:

```typescript
// 错误：/api/auth/me 在 publicPaths 中，preHandler 跳过解析
app.get('/api/auth/me', async (request, reply) => {
  // request.currentUser 永远为 null（preHandler 被跳过）
  return reply.send({ user: request.currentUser }); // ❌ 返回 null user
});

// 正确：/api/auth/me 不在 publicPaths 中，走正常 token 解析
app.get('/api/auth/me', async (request, reply) => {
  // preHandler 已解析 token 写入 request.currentUser
  if (!request.currentUser) {
    return reply.code(401).send({ error: 'Unauthorized' }); // ✅ authGuard 返回 401
  }
  return reply.send({ user: request.currentUser });
});
```

### BR-049-2：publicPaths 配置位置必须集中管理

- **Severity**: suggestion
- **Description**: `publicPaths` 配置必须在认证中间件初始化处集中管理（如 `setupAuthMiddleware(app, { publicPaths })`），禁止散落在多处（如路由文件内联、handler 内判断、配置文件分散定义）。散落配置会导致：① 修改时遗漏；② 评审时难以全面核查；③ 同一端点在不同位置可能被同时声明为 public 和 private。评审时确认 `publicPaths` 只在认证中间件初始化处定义一次，且值从 config 读取（禁止字面量硬编码）。
- **Suggested fix**:

```typescript
// 错误：publicPaths 散落在多处
// routes/auth.ts
app.get('/api/auth/me', { config: { public: true } }, handler); // ❌ 散落声明
// middleware/auth.ts
setupAuthMiddleware(app, { publicPaths: ['/api/auth/login', '/health'] });

// 正确：publicPaths 集中在认证中间件初始化处，从 config 读取
// config: auth_endpoint_classification.public_paths_whitelist = '/api/auth/login,/health'
const publicPaths = config.auth_endpoint_classification.public_paths_whitelist.split(',');
setupAuthMiddleware(app, { publicPaths }); // ✅ 单点配置
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `auth_endpoint_classification.enabled` | `true` | 是否启用本组规则（BR-048~049） |
| `auth_endpoint_classification.severity` | `critical` | 违规严重级别（critical = 安全漏洞） |
| `auth_endpoint_classification.public_paths_whitelist` | `/api/auth/login,/health` | 完全公开端点列表（逗号分隔） |
| `auth_endpoint_classification.auth_required_endpoints` | `/api/auth/me,/api/auth/logout` | 需鉴权端点示例列表（用于识别误放入 publicPaths 的端点） |
| `auth_endpoint_classification.middleware_hook` | `preHandler` | 认证中间件 hook 名称 |
| `auth_endpoint_classification.skip_mechanism` | `isPublicPath` | 跳过 token 解析的机制名称 |

## 检查方式

1. 用 Grep 在认证中间件初始化处（如 `middleware/auth.ts`、`setupAuthMiddleware` 调用处）检索 `publicPaths` 关键字，提取 `publicPaths` 数组内容。
2. 用 Grep 检索 `auth_required_endpoints`（默认 `/api/auth/me,/api/auth/logout`）中的每个端点路径，确认未出现在 `publicPaths` 中：
   - 出现 → **BR-048-1 违规**（需鉴权端点放入 publicPaths）
   - 未出现 → 继续
3. **BR-048-2 检查**：评审 `publicPaths` 中每个路径的语义，确认都是"无登录态也能返回有意义响应"的端点（如 login/health）；若包含 `/api/auth/me` 等获取当前用户信息的端点 → **BR-048-2 违规**（反直觉陷阱）。
4. **BR-049-1 检查**：用 Grep 在 `auth_required_endpoints` 列表对应的路由 handler 中检索 `request.currentUser`：
   - 命中且 handler 内有 `if (!request.currentUser)` 守卫 → 通过
   - 命中但无守卫 → suggestion（建议增加空值守卫）
   - 未命中 → 跳过（handler 未使用 currentUser）
5. **BR-049-2 检查**：用 Grep 在整个 `api/` 目录检索 `publicPaths` 关键字：
   - 仅在认证中间件初始化处出现 → 通过
   - 在多个文件出现 → **BR-049-2 违规**（配置散落）
6. 用 Grep 检索 `publicPaths` 数组内是否含字面量字符串（如 `'/api/auth/login'` 字面量）而非从 config 读取：
   - 字面量硬编码 → suggestion（建议参数化从 config 读取）

## 正确示例

```typescript
// middleware/auth.ts —— 完整合规实现
import { config } from '../config/index.js';

// 从 config 读取 publicPaths（禁止字面量硬编码）
// config: auth_endpoint_classification.public_paths_whitelist = '/api/auth/login,/health'
const publicPaths = config.auth_endpoint_classification.public_paths_whitelist.split(',');

export function setupAuthMiddleware(app: FastifyInstance): void {
  // publicPaths 集中在认证中间件初始化处定义一次
  app.addHook('preHandler', async (request, reply) => {
    // isPublicPath 跳过机制：publicPaths 中的路径跳过 token 解析
    if (isPublicPath(request.url, publicPaths)) {
      return; // 跳过 token 解析，currentUser 保持 null
    }
    // 非公开路径走正常 token 解析
    const token = extractToken(request);
    if (token) {
      request.currentUser = await verifyToken(token);
    }
  });
}

// routes/auth.ts —— /api/auth/me 走正常 token 解析（不在 publicPaths 中）
app.get('/api/auth/me', async (request, reply) => {
  // preHandler 已解析 token 写入 currentUser（未登录时为 null）
  if (!request.currentUser) {
    return reply.code(401).send({ error: 'Unauthorized' }); // authGuard 返回 401
  }
  return reply.send({ user: request.currentUser });
});
```

## 错误示例

```typescript
// 错误 1：/api/auth/me 误放入 publicPaths（BR-048-1 违规）
setupAuthMiddleware(app, {
  publicPaths: ['/api/auth/login', '/health', '/api/auth/me'], // ❌ me 不能放入
});
// 结果：preHandler 跳过 token 解析，request.currentUser 永远为 null
// /api/auth/me handler 内 authGuard 因 currentUser 为 null 必然返回 401

// 错误 2：误以为 publicPaths = "放行已登录用户"（BR-048-2 违规，反直觉陷阱）
// 实际语义：publicPaths = "跳过 token 解析，currentUser 永远 null"
setupAuthMiddleware(app, {
  publicPaths: ['/api/auth/login', '/health', '/api/auth/me'], // ❌ 反直觉
});

// 错误 3：/api/auth/me 跳过解析后返回 null user（BR-049-1 违规）
app.get('/api/auth/me', async (request, reply) => {
  return reply.send({ user: request.currentUser }); // ❌ 永远返回 null
});

// 错误 4：publicPaths 散落在多处（BR-049-2 违规）
// routes/auth.ts
app.get('/api/auth/me', { config: { public: true } }, handler); // ❌ 散落声明
// middleware/auth.ts
setupAuthMiddleware(app, { publicPaths: ['/api/auth/login', '/health'] });

// 错误 5：publicPaths 字面量硬编码（参数化建议）
setupAuthMiddleware(app, {
  publicPaths: ['/api/auth/login', '/health'], // ❌ 字面量硬编码，应从 config 读取
});
```

## 适配新项目

- **Express 项目**：`middleware_hook` 改为 `use`，`skip_mechanism` 改为 `path match`；`setupAuthMiddleware` 改为 `app.use(authMiddleware)`。
- **Koa 项目**：`middleware_hook` 改为 `app.use`，`skip_mechanism` 改为 `ctx.path match`。
- **NestJS 项目**：`middleware_hook` 改为 `Guard`，`skip_mechanism` 改为 `@Public()` 装饰器；`publicPaths` 改为 `@Public()` 装饰的 controller/method 列表。
- **无认证应用**：`auth_endpoint_classification.enabled` 设为 `false`，跳过本组规则。
- **多角色 RBAC 项目**：`auth_required_endpoints` 扩展为 `{ path, roles }[]`，preHandler 解析 token 后还需校验角色，但 `publicPaths` 语义不变（仍只含完全公开端点）。
- **微服务网关项目**：`publicPaths` 在网关层集中配置，下游服务不重复定义；网关 preHandler 解析 token 后通过 header 传递 `currentUser`，下游服务从 header 读取。
