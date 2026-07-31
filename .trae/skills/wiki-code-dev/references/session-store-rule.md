# 会话存储双层淘汰 + 防篡改规则（CODING-061）

> 复盘来源：v3 媒体生成工具开发中，内存 Map 存储用户会话（含 LLM 上下文与生成产物引用），曾出现两类问题：①会话数量无限增长导致内存溢出；②前端归档接口直接接收客户端传的答案内容，存在篡改风险（用户可伪造答案内容覆盖服务端记录）。改用双层淘汰（TTL + LRU）+ 引用模式（客户端只传 sessionId + messageIndex，内容从服务端取）。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `session_store` 字段读取，禁止在规则文件中硬编码上限或 TTL。

## 规则

**内存 Map 存储会话/缓存数据必须遵守四项契约**：

1. **双层淘汰**：内存 Map 必须实现双层淘汰策略——先按 TTL 淘汰过期项，仍超上限按插入顺序（`Map.keys().next()`）淘汰最早项
2. **上限与 TTL**：会话上限 `session_store.max_sessions`（默认 100），TTL `session_store.ttl_ms`（默认 3600000ms / 1 小时）
3. **引用模式**：归档/查询类接口不接收客户端传内容，只接收引用（`sessionId` + `messageIndex`），内容从服务端 sessions 取
4. **防篡改**：`session_store.trust_client_content`（默认 `false`）为 false 时，客户端传的内容字段必须被忽略，仅信任服务端 sessions 中的内容

## 适用场景

- 内存 Map 存储用户会话（LLM 上下文、生成产物引用、对话历史）
- 多用户并发访问的服务进程（需防止内存无限增长）
- 归档/查询接口需引用历史会话内容（防止客户端篡改）
- 任何需要"服务端权威源 + 客户端引用"的存储场景

## 不适用场景

- 外部缓存（Redis/Memcached，自带 TTL 与 LRU）
- 持久化存储（数据库/文件系统，无需内存淘汰）
- 单次请求内的临时变量（请求结束即释放，无需淘汰）
- 客户端本地存储（localStorage/IndexedDB，浏览器自管理）
- 只读缓存（无写入，无需淘汰）

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `session_store.enabled` | `true` | 是否启用会话存储守卫 |
| `session_store.severity` | `error` | 违规严重级别 |
| `session_store.max_sessions` | `100` | 会话数量上限（超过触发 LRU 淘汰） |
| `session_store.ttl_ms` | `3600000` | 会话 TTL（毫秒，默认 1 小时） |
| `session_store.trust_client_content` | `false` | 是否信任客户端传的内容字段 |
| `session_store.evict_strategy` | `ttl-then-lru` | 淘汰策略（先 TTL 后 LRU） |
| `session_store.reference_fields` | `sessionId,messageIndex` | 引用模式接受的字段列表 |

## 检查方式

1. **双层淘汰检查**：写入会话后必须先按 TTL 淘汰过期项，再判断是否超 `max_sessions`，超限则 `Map.delete(Map.keys().next().value)` 淘汰最早
2. **上限检查**：`Map.size` 必须始终 ≤ `max_sessions`，禁止无限增长
3. **引用模式检查**：归档/查询接口的请求体 schema 只接受 `reference_fields`，不接受 `content` / `answer` / `result` 等内容字段
4. **防篡改检查**：`trust_client_content` 为 false 时，即使客户端传了内容字段也必须被忽略，内容从服务端 `sessions.get(sessionId).messages[messageIndex]` 取
5. **TTL 检查**：会话写入时必须记录 `expiresAt = Date.now() + ttl_ms`，读取时检查过期则删除并返回 null

## 正确示例

```typescript
// services/api/src/services/session-service.ts
import { config } from '../config.js';

const ss = config.session_store;

interface SessionMessage {
  role: 'user' | 'assistant';
  content: string;
  outputMode?: string;
  file?: string;
}

interface Session {
  id: string;
  messages: SessionMessage[];
  createdAt: number;
  expiresAt: number;
}

/**
 * 会话存储——双层淘汰 + 防篡改
 * 为什么用双层淘汰：单 TTL 会导致短时间内大量会话未过期但内存已满；
 * 单 LRU 会导致长期未访问但仍在用的会话被误淘汰。双层策略兼顾时效与容量。
 */
class SessionStore {
  private sessions = new Map<string, Session>();

  set(id: string, session: Session): void {
    // ✅ 第一层：TTL 淘汰过期项
    this.evictExpired();

    // ✅ 写入新会话（先写再判断，避免边界条件）
    session.expiresAt = Date.now() + ss.ttl_ms;
    this.sessions.set(id, session);

    // ✅ 第二层：LRU 淘汰（仍超上限则淘汰最早）
    while (this.sessions.size > ss.max_sessions) {
      const oldest = this.sessions.keys().next().value;
      if (oldest === undefined) break;
      this.sessions.delete(oldest);
    }
  }

  get(id: string): Session | null {
    const s = this.sessions.get(id);
    if (!s) return null;
    // ✅ 读取时检查 TTL
    if (Date.now() > s.expiresAt) {
      this.sessions.delete(id);
      return null;
    }
    return s;
  }

  private evictExpired(): void {
    const now = Date.now();
    for (const [id, s] of this.sessions) {
      if (now > s.expiresAt) this.sessions.delete(id);
    }
  }
}

export const sessionStore = new SessionStore();
```

```typescript
// services/api/src/routes/archive.ts
// ✅ 归档接口：引用模式，不接收客户端传内容
app.post('/api/archive', async (request, reply) => {
  const { sessionId, messageIndex } = request.body as {
    sessionId: string;
    messageIndex: number;
  };

  // ✅ 内容从服务端 sessions 取，客户端无法篡改
  const session = sessionStore.get(sessionId);
  if (!session) {
    return reply.code(404).send({ error: 'session not found' });
  }
  const message = session.messages[messageIndex];
  if (!message) {
    return reply.code(404).send({ error: 'message not found' });
  }

  // ✅ 即便客户端传了 content 字段也忽略（trust_client_content = false）
  const archivePath = archiveMediaProduct({
    outputMode: message.outputMode as 'image' | 'ppt' | 'video',
    prompt: message.content,
    file: message.file!,
  });
  return reply.send({ ok: true, path: archivePath });
});
```

## 错误示例

```typescript
// ❌ 错误：无淘汰策略，会话无限增长导致内存溢出
class SessionStore {
  private sessions = new Map<string, Session>();
  set(id: string, s: Session) {
    this.sessions.set(id, s); // ⚠️ 无上限，无 TTL，内存终将溢出
  }
}

// ❌ 错误：只按 TTL 淘汰，短期大量会话未过期但内存已满
set(id: string, s: Session) {
  this.evictExpired();
  this.sessions.set(id, s);
  // ⚠️ 缺少 LRU 淘汰，max_sessions 检查缺失
}

// ❌ 错误：归档接口接收客户端传的 content，存在篡改风险
app.post('/api/archive', async (request, reply) => {
  const { sessionId, content, outputMode } = request.body as {
    sessionId: string;
    content: string;     // ⚠️ 客户端可伪造内容
    outputMode: string;
  };
  // ⚠️ 直接用客户端传的 content 归档，服务端记录可被覆盖
  archiveMediaProduct({ outputMode, prompt: content, file: '' });
});

// ❌ 错误：读取时不检查 TTL，返回过期会话
get(id: string): Session | null {
  return this.sessions.get(id) ?? null; // ⚠️ 未检查 expiresAt
}
```

## 适配新项目

- 适配 Redis：`max_sessions` 与 `ttl_ms` 改为 Redis 配置，淘汰策略由 Redis 自管理（`maxmemory-policy: allkeys-lru`）
- 适配数据库持久化：会话写入数据库，TTL 用 `expire_at` 字段查询过滤，无需内存淘汰
- 适配无状态服务：会话存到 JWT 或客户端 cookie（签名防篡改），服务端不存会话
- 适配高并发：用 LRU cache 库（如 `lru-cache` npm 包）替代手写 Map，线程安全且性能更优
- 适配长会话场景：`ttl_ms` 调大到 24 小时或更长，`max_sessions` 按用户数估算

## 与其他规则的关系

- 与 CODING-060（媒体归档 frontmatter 标准化）联动：归档接口用本规则的引用模式取内容，再用 CODING-060 的 frontmatter 标准归档
- 与 CODING-059（长/短任务架构分离）联动：长任务进行中的中间状态存入会话，任务完成后归档
- 与 CODING-062（prompt 单点存储）联动：会话中的 prompt 内容从 prompts/ 目录加载，不在源码内联
- 与项目硬约束（单一权威源）联动：会话类数据权威源为后端 `data/`，浏览器存储仅作降级缓存
- 与 CODING-013（优雅停止）联动：服务退出时会话不持久化（短 TTL），重启后客户端需重新发起会话
