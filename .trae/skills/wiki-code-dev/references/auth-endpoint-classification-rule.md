# 认证端点分类守卫规则（CODING-054）

> 复盘来源：Skill 导入模块开发中，携带有效 token 调用 `/api/auth/me` 返回 401。根因是 `/api/auth/me` 被错误放入 `publicPaths` 白名单，导致全局 `preHandler` 跳过 token 解析，`currentUser` 永远为 null，authGuard 必然返回 401。这是反直觉陷阱——看似"公开"的端点放入白名单后反而导致认证失效。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `auth_endpoint_classification` 字段读取，禁止在规则文件中硬编码端点路径或中间件 hook 名称。

## 规则

**需鉴权端点禁止放入 publicPaths 白名单**：`auth_endpoint_classification.public_paths_whitelist` 只能包含完全公开端点（如 login / health）。任何需要读取当前用户身份的端点（如 me / logout / profile）放入白名单后，全局 `auth_endpoint_classification.middleware_hook`（默认 `preHandler`）会通过 `auth_endpoint_classification.skip_mechanism`（默认 `isPublicPath`）跳过 token 解析，导致 `currentUser` 永远为 null，authGuard 必然返回 401。

## 适用场景

- 所有带 RBAC / authGuard 的后端框架（Fastify / Express / Koa / NestJS）
- 全局 preHandler / middleware 中根据 `publicPaths` 白名单跳过 token 解析的架构
- 新增认证相关端点（login / logout / me / profile / refresh / register）时
- Code Review 涉及 `publicPaths` / `publicRoutes` / `whitelist` 配置变更时
- 排查"携带有效 token 调用接口却返回 401"类问题时

## 不适用场景

- 完全无认证的公开 API（无 token 解析逻辑，无白名单概念）
- 端点级独立鉴权（每个端点单独写 token 解析，不依赖全局跳过机制）
- 第三方网关层鉴权（如 API Gateway / Nginx auth_request，应用层不感知白名单）
- WebSocket 握手鉴权（连接建立时一次性鉴权，无 per-request 跳过机制）

## 前置检查流程

```
新增/修改认证端点:
   ↓
1. 判断端点是否需要读取当前用户身份（currentUser / req.user）
   ↓
   需要读取 → 该端点禁止放入 publicPaths 白名单（直接结束）
   ↓
   不需要读取（完全公开，如 login / health）→ 可以放入 publicPaths 白名单
   ↓
2. 审查 publicPaths 白名单当前内容
   ↓
   白名单中存在需鉴权端点 → 立即移除，仅保留完全公开端点
   ↓
3. 验证：携带有效 token 调用需鉴权端点，确认返回 200 而非 401
   ↓
4. 验证：不携带 token 调用需鉴权端点，确认返回 401（鉴权生效）
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `auth_endpoint_classification.enabled` | `true` | 是否启用认证端点分类守卫 |
| `auth_endpoint_classification.severity` | `error` | 违规严重级别（error = 必须修复） |
| `auth_endpoint_classification.public_paths_whitelist` | `/api/auth/login,/health` | 完全公开端点列表（逗号分隔，仅放无需鉴权的端点） |
| `auth_endpoint_classification.auth_required_pattern` | `/api/auth/me,/api/auth/logout` | 需鉴权端点示例列表（用于识别"看似公开实则需鉴权"的端点） |
| `auth_endpoint_classification.middleware_hook` | `preHandler` | 认证中间件 hook 名称（Fastify 用 preHandler，Express 用 use） |
| `auth_endpoint_classification.skip_mechanism` | `isPublicPath` | 跳过 token 解析的机制名称（白名单匹配函数名） |

## 检查方式

1. **白名单审查**：`public_paths_whitelist` 中每一项必须是完全公开端点（无需读取用户身份），禁止包含 `/me` / `/logout` / `/profile` 等需鉴权端点
2. **端点分类二分法**：新增端点时必须明确分类——"完全公开"（入白名单）或"需鉴权"（不入白名单，由全局 preHandler 解析 token）
3. **回归验证**：修改 `public_paths_whitelist` 后必须用有效 token 调用所有需鉴权端点，确认返回 200；用无 token 调用确认返回 401
4. **静态扫描**：CI 中扫描 `auth_required_pattern` 列表中的端点是否出现在 `public_paths_whitelist` 中，命中即报错

## 正确示例

```typescript
// services/api/src/index.ts — Fastify 全局 preHandler
// 完全公开端点才进白名单，需鉴权端点（me/logout）禁止入内
const publicPaths = ['/api/auth/login', '/health']; // 从配置读取

server.addHook('preHandler', async (request, reply) => {
  // ✅ 仅完全公开端点跳过 token 解析
  if (publicPaths.includes(request.url.split('?')[0])) {
    return; // login/health 无需 currentUser
  }
  // 需鉴权端点（me/logout/profile）会走到这里，解析 token 设置 currentUser
  const token = extractToken(request);
  if (token) {
    request.currentUser = await verifyToken(token);
  }
});

// /api/auth/me 路由 — 不在白名单中，preHandler 会解析 token
server.get('/api/auth/me', async (request, reply) => {
  // ✅ authGuard 检查 currentUser，有效 token 时 currentUser 非空，返回 200
  if (!request.currentUser) {
    return reply.code(401).send({ error: 'Unauthorized' });
  }
  return { user: request.currentUser };
});
```

```typescript
// 配置从 config 读取，禁止硬编码端点路径
import { config } from './config.js';
// ✅ 白名单来源单一，从 config 读取
const publicPaths = config.auth_endpoint_classification.public_paths_whitelist.split(',');
const authRequiredPattern = config.auth_endpoint_classification.auth_required_pattern.split(',');

// CI 静态检查：需鉴权端点不应出现在白名单中
function validatePublicPaths() {
  const violations = authRequiredPattern.filter(p => publicPaths.includes(p));
  if (violations.length > 0) {
    throw new Error(`需鉴权端点误入 publicPaths 白名单: ${violations.join(', ')}`);
  }
}
```

## 错误示例

```typescript
// ❌ 错误：/api/auth/me 放入 publicPaths 白名单
const publicPaths = ['/api/auth/login', '/health', '/api/auth/me']; // me 不该在此

server.addHook('preHandler', async (request, reply) => {
  if (publicPaths.includes(request.url.split('?')[0])) {
    return; // ⚠️ me 命中白名单，跳过 token 解析，currentUser 永远 null
  }
  // ... token 解析逻辑被跳过
});

server.get('/api/auth/me', async (request, reply) => {
  // ❌ request.currentUser 永远是 null（preHandler 跳过了 token 解析）
  // 即使携带有效 token，authGuard 也必然返回 401
  if (!request.currentUser) {
    return reply.code(401).send({ error: 'Unauthorized' }); // 必然走到这里
  }
  return { user: request.currentUser }; // 永远不会执行
});
```

```typescript
// ❌ 错误：硬编码端点路径，未从 config 读取
const publicPaths = ['/api/auth/login', '/health']; // 硬编码，无法适配新项目
```

## 适配新项目

- 适配 Express：`middleware_hook` 改为 `use`，`skip_mechanism` 改为 `path match`（Express middleware 用 `app.use` 注册，跳过逻辑用路径匹配）
- 适配 Koa：`middleware_hook` 改为 `app.use`，`skip_mechanism` 改为 `ctx.path match`
- 适配 NestJS：`middleware_hook` 改为 `Guard`，`skip_mechanism` 改为 `Public decorator`（用 `@Public()` 装饰器标记公开端点，而非路径白名单）
- 适配无认证应用：`enabled` 设为 `false`（无 token 解析逻辑，无白名单概念）
- 适配网关层鉴权：`enabled` 设为 `false`（应用层不感知白名单，由网关统一鉴权）

## 与其他规则的关系

- 与 CODING-011（路由注册守卫）联动：新增认证路由时，既要完成路由注册（CODING-019），又要正确分类端点（CODING-054），避免误入白名单
- 与 CODING-014（敏感字段脱敏）联动：`/api/auth/me` 等需鉴权端点返回的用户信息中，敏感字段（token / password）必须脱敏
- 与 PowerShell 约束规则联动：PowerShell 脚本中用 `Invoke-WebRequest` + Bearer header 验证需鉴权端点时，token 必须正确传递（白名单端点无需 token，需鉴权端点必须带 token）
- 与配置读取一致性参数联动：`public_paths_whitelist` 的读取入口必须统一（单一读取函数），避免多处硬编码导致白名单不一致
