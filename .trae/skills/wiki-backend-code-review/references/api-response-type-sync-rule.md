# API 响应类型同步检查（BR-026）

> 复盘来源：后端新增 API 端点或修改响应形状后，前端 types.ts 未同步更新，导致前端编译期无错误但运行时访问 `undefined` 字段、表单提交缺字段、类型断言失败。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"api_response_type_sync"章节读取，禁止在本规则文件硬编码具体路径或接口名。

## Trigger Keywords
reply.send, reply.raw.write, return result, response shape, API contract, routes/*.ts, types.ts, export interface, reply.code, FastifyReply

## Rules

### BR-026-1: API 端点响应形状必须与前端 types.ts 中对应 interface 同步

- **Severity**: critical
- **Description**: 新增或修改 API 端点时，后端 `reply.send(...)` 返回的对象形状必须与前端 `frontend_types_path` 中对应 interface 的字段名、类型签名、可选性（`?`）完全一致。前端 TypeScript 编译器独立解析 `types.ts`，后端形状变更不会触发前端编译错误，仅在运行时暴露为 `undefined` 字段或类型断言失败，难以定位。
- **Suggested fix**:
```typescript
// api/src/routes/conversation.ts —— 后端响应形状
import type { ConversationMeta } from '../types.js';

app.get('/api/conversations/:id', async (request, reply) => {
  const meta: ConversationMeta = await loadMeta(request.params.id);
  // 响应形状与 ConversationMeta interface 一一对应
  return reply.send(meta);
});

// frontend/src/types.ts —— 前端 interface 同步
export interface ConversationMeta {
  id: string;
  title: string;
  updatedAt: string;
  tokenCount: number; // 后端新增字段时前端必须同步
}
```

### BR-026-2: 新增响应字段必须在前后端同步添加

- **Severity**: critical
- **Description**: 后端在响应对象中新增字段时，前端 `frontend_types_path` 对应 interface 必须在同一 PR 中同步新增该字段，字段名、类型、可选性保持一致。禁止"后端先加字段、前端后续补"的渐进式做法——任何中间状态的 PR 都会让前端访问到 `undefined` 字段。若字段为可选（后端可能不返回），前端必须用 `field?: T` 标注，不能用 `field: T` 强制非空。
- **Suggested fix**:
```typescript
// 后端：新增 tokenCount 字段
app.get('/api/conversations/:id', async (request, reply) => {
  const meta = await loadMeta(request.params.id);
  return reply.send({
    ...meta,
    tokenCount: meta.tokens, // 新增字段
  });
});

// 前端：同步新增（同一 PR）
export interface ConversationMeta {
  id: string;
  title: string;
  updatedAt: string;
  tokenCount: number; // 与后端字段名/类型一致
}
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `api_response_type_sync.enabled` | `true` | 是否启用本规则 |
| `api_response_type_sync.severity` | `critical` | 违规严重级别 |
| `api_response_type_sync.backend_routes_directory` | `api/src/routes/` | 后端路由文件目录（相对项目根） |
| `api_response_type_sync.frontend_types_path` | `frontend/src/types.ts` | 前端 types 文件路径（相对项目根） |
| `api_response_type_sync.backend_types_path` | `api/src/types.ts` | 后端 types 文件路径（相对项目根），用于提取共享 interface |
| `api_response_type_sync.reply_send_pattern` | `reply\.send\|return reply\.` | reply.send 调用匹配模式（正则字面量） |
| `api_response_type_sync.monorepo_import_type_exempt` | `true` | monorepo 前端直接 `import type` 引用后端类型时豁免本规则 |

## 检查方式

1. 用 Grep 检索 `api_response_type_sync.backend_routes_directory` 下所有 `.ts` 文件中匹配 `api_response_type_sync.reply_send_pattern` 的位置。
2. 对每个 `reply.send(...)` 调用，提取传入对象形状（字段名 + 是否可选 + 字面量类型）。
3. 用 Read 读取 `api_response_type_sync.frontend_types_path`，提取所有 `export interface` 定义。
4. 对比后端响应形状与前端 interface：
   - 后端返回字段在前端 interface 中缺失 → BR-026-1 违规
   - 后端新增字段但前端 interface 未同步 → BR-026-2 违规
   - 字段可选性不一致（后端必返、前端标 `?`，或反之）→ BR-026-1 违规
5. 若 `api_response_type_sync.monorepo_import_type_exempt` 为 `true`，且前端通过 `import type { ... } from '../../api/src/types.js'` 直接引用后端类型，则豁免本规则——单源定义即保证一致。

## 正确示例

```typescript
// api/src/routes/ai.ts —— 后端响应形状
import type { AiConfigResponse } from '../types.js';

app.get('/api/ai/config', async (request, reply) => {
  const config = await loadAiConfig();
  const response: AiConfigResponse = {
    provider: config.provider,
    baseUrl: config.baseUrl,
    model: config.model,
    apiKey: mask(config.apiKey),       // 脱敏字段
    apiKeyConfigured: Boolean(config.apiKey),
  };
  return reply.send(response);
});

// frontend/src/types.ts —— 前端 interface 同步
export interface AiConfigResponse {
  provider: string;
  baseUrl: string;
  model: string;
  apiKey: string;             // 脱敏值，与后端一致
  apiKeyConfigured: boolean;  // 标志位，与后端一致
}
```

## 错误示例

```typescript
// 错误 1：后端新增字段，前端未同步
// api/src/routes/ai.ts
app.get('/api/ai/config', async (request, reply) => {
  return reply.send({
    provider: 'openai',
    baseUrl: 'https://api.openai.com',
    model: 'gpt-4',
    apiKey: '****1234',
    apiKeyConfigured: true,
    quotaRemaining: 500,  // 新增字段，前端 types.ts 未同步
  });
});

// frontend/src/types.ts —— 缺 quotaRemaining 字段
export interface AiConfigResponse {
  provider: string;
  baseUrl: string;
  model: string;
  apiKey: string;
  apiKeyConfigured: boolean;
  // ❌ 缺 quotaRemaining，前端访问 response.quotaRemaining 得到 undefined
}

// 错误 2：可选性不一致
// 后端必返字段，前端标可选
// frontend/src/types.ts
export interface ConversationMeta {
  id: string;
  title: string;
  updatedAt?: string;  // ❌ 后端 reply.send 必返回 updatedAt，前端标 ? 导致类型守卫错误
}
```

## 适配新项目

- **Express 项目**：将 `reply.send(...)` 替换为 `res.json(...)`，`reply_send_pattern` 调整为 `res\.json\(|return res\.`，其余规则不变。
- **NestJS 项目**：控制器方法返回的对象形状即响应形状（`@Get() findOne(): ResponseDto`），将 `reply_send_pattern` 调整为 `return\s+\{` 或检查 `@ApiResponse` 装饰器与 DTO 类的字段一致性；`backend_routes_directory` 改为 `src/controllers/` 或 `src/modules/*/controllers/`。
- **Koa 项目**：将 `reply.send(...)` 替换为 `ctx.body = ...`，`reply_send_pattern` 调整为 `ctx\.body\s*=`，其余规则不变。
- **GraphQL 项目**：类型由 schema 自动生成，本规则不适用，可在 `enabled` 设为 `false`。
- **monorepo 共享类型项目**：若前端通过 `import type` 直接引用后端 `types.ts`，将 `monorepo_import_type_exempt` 设为 `true` 豁免本规则。
