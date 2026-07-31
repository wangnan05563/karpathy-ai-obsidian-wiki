# 会话存储双层淘汰审查规则（BR-059）

> 复盘来源：v3 媒体生成工具开发中，内存 Map 存储用户会话（含 LLM 上下文与生成产物引用），曾出现两类问题：①会话数量无限增长导致内存溢出；②前端归档接口直接接收客户端传的答案内容，存在篡改风险（用户可伪造答案内容覆盖服务端记录）。改用双层淘汰（TTL + LRU）+ 引用模式（客户端只传 sessionId + messageIndex，内容从服务端取）（CODING-061）。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"会话存储双层淘汰审查参数（session_store_review）"章节读取，禁止在本规则文件硬编码上限或 TTL。

## Trigger Keywords

new Map(, Map.set, Map.delete, Map.keys().next(), sessions, session, max_sessions, ttl_ms, expiresAt, evictExpired, LRU, TTL, sessionId, messageIndex, trust_client_content, content, answer, result, 防篡改, 引用模式, 内存溢出

## Rules

### BR-059-1：内存 Map 必须实现双层淘汰（TTL + LRU），禁止无限增长

- **Severity**: critical
- **Description**: 内存 Map 存储会话/缓存数据必须实现双层淘汰策略——先按 TTL 淘汰过期项，仍超 `session_store_review.max_sessions`（默认 100）上限按插入顺序（`Map.keys().next()`）淘汰最早项。无淘汰策略的 Map 会无限增长导致内存溢出。评审时确认：会话存储类/函数有 `evictExpired()` TTL 淘汰 + `while (size > max) Map.delete(Map.keys().next().value)` LRU 淘汰。
- **Suggested fix**:

```typescript
// 错误：无淘汰策略，会话无限增长导致内存溢出
class SessionStore {
  private sessions = new Map<string, Session>();
  set(id: string, s: Session) {
    this.sessions.set(id, s); // ❌ 无上限，无 TTL，内存终将溢出
  }
}

// 正确：双层淘汰（TTL + LRU）
const ss = config.session_store_review;
class SessionStore {
  private sessions = new Map<string, Session>();
  set(id: string, session: Session): void {
    // ✅ 第一层：TTL 淘汰过期项
    this.evictExpired();
    // ✅ 写入新会话
    session.expiresAt = Date.now() + ss.ttl_ms;
    this.sessions.set(id, session);
    // ✅ 第二层：LRU 淘汰（仍超上限则淘汰最早）
    while (this.sessions.size > ss.max_sessions) {
      const oldest = this.sessions.keys().next().value;
      if (oldest === undefined) break;
      this.sessions.delete(oldest);
    }
  }
  private evictExpired(): void {
    const now = Date.now();
    for (const [id, s] of this.sessions) {
      if (now > s.expiresAt) this.sessions.delete(id);
    }
  }
}
```

### BR-059-2：读取时必须检查 TTL，禁止返回过期会话

- **Severity**: critical
- **Description**: 读取会话时必须检查 `expiresAt`，过期则删除并返回 null。未检查 TTL 会返回过期会话，导致业务逻辑用过期数据做决策。评审时确认：`get()` 方法有 `if (Date.now() > s.expiresAt) { delete; return null; }` 逻辑。
- **Suggested fix**:

```typescript
// 错误：读取时不检查 TTL，返回过期会话
get(id: string): Session | null {
  return this.sessions.get(id) ?? null; // ❌ 未检查 expiresAt
}

// 正确：读取时检查 TTL
get(id: string): Session | null {
  const s = this.sessions.get(id);
  if (!s) return null;
  if (Date.now() > s.expiresAt) { // ✅ 检查过期
    this.sessions.delete(id);
    return null;
  }
  return s;
}
```

### BR-059-3：归档/查询接口必须用引用模式，禁止接收客户端传内容

- **Severity**: critical
- **Description**: 归档/查询类接口不接收客户端传内容字段（`content` / `answer` / `result`），只接收引用（`sessionId` + `messageIndex`），内容从服务端 sessions 取。`session_store_review.trust_client_content`（默认 `false`）为 false 时，客户端传的内容字段必须被忽略。接收客户端传内容存在篡改风险（用户可伪造答案内容覆盖服务端记录）。评审时确认：归档/查询接口的请求体 schema 只接受 `reference_fields`（sessionId, messageIndex），不接受内容字段。
- **Suggested fix**:

```typescript
// 错误：归档接口接收客户端传的 content，存在篡改风险
app.post('/api/archive', async (request, reply) => {
  const { sessionId, content, outputMode } = request.body as {
    sessionId: string; content: string; outputMode: string; // ❌ 客户端可伪造内容
  };
  archiveMediaProduct({ outputMode, prompt: content, file: '' }); // ❌ 直接用客户端传的 content
});

// 正确：引用模式，内容从服务端 sessions 取
app.post('/api/archive', async (request, reply) => {
  const { sessionId, messageIndex } = request.body as {
    sessionId: string; messageIndex: number; // ✅ 只接受引用字段
  };
  const session = sessionStore.get(sessionId);
  if (!session) return reply.code(404).send({ error: 'session not found' });
  const message = session.messages[messageIndex];
  if (!message) return reply.code(404).send({ error: 'message not found' });
  // ✅ 内容从服务端取，客户端无法篡改
  archiveMediaProduct({ outputMode: message.outputMode, prompt: message.content, file: message.file! });
});
```

### BR-059-4：trust_client_content 为 false 时客户端传的内容字段必须被忽略

- **Severity**: critical
- **Description**: `session_store_review.trust_client_content`（默认 `false`）为 false 时，即使客户端传了 `content` / `answer` / `result` 等内容字段也必须被忽略，仅信任服务端 sessions 中的内容。评审时确认：归档/查询接口的请求体解构中无内容字段，或即便客户端传了也未被使用。
- **Suggested fix**:

```typescript
// 错误：trust_client_content = false 但仍使用客户端传的 content
app.post('/api/archive', async (request, reply) => {
  const { sessionId, messageIndex, content } = request.body; // ❌ 解构了 content
  // 即便 messageIndex 存在，content 字段的存在本身就是安全隐患
  if (content) { archiveWith(content); } // ❌ 使用了客户端传的 content
});

// 正确：忽略客户端传的 content 字段
app.post('/api/archive', async (request, reply) => {
  const { sessionId, messageIndex } = request.body; // ✅ 只解构引用字段
  // ✅ 即便客户端传了 content 也被忽略（未解构）
  const session = sessionStore.get(sessionId);
  const message = session.messages[messageIndex];
  archiveMediaProduct({ prompt: message.content }); // ✅ 用服务端内容
});
```

### BR-059-5：会话写入时必须记录 expiresAt，禁止无 TTL 写入

- **Severity**: suggestion
- **Description**: 会话写入时必须记录 `expiresAt = Date.now() + ttl_ms`，禁止无 TTL 写入。无 TTL 的会话永不过期，只能靠 LRU 淘汰，长期运行会导致活跃会话被误淘汰。评审时确认：`set()` 方法中有 `session.expiresAt = Date.now() + ss.ttl_ms` 赋值。
- **Suggested fix**:

```typescript
// 错误：无 TTL 写入，会话永不过期
set(id: string, session: Session) {
  this.sessions.set(id, session); // ❌ 未设置 expiresAt
}

// 正确：写入时记录 expiresAt
set(id: string, session: Session): void {
  session.expiresAt = Date.now() + ss.ttl_ms; // ✅ 设置 TTL
  this.sessions.set(id, session);
}
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `session_store_review.enabled` | `true` | 是否启用本组规则（BR-059） |
| `session_store_review.severity_br059_1` | `critical` | BR-059-1 无淘汰策略违规严重级别 |
| `session_store_review.severity_br059_2` | `critical` | BR-059-2 未检查 TTL 违规严重级别 |
| `session_store_review.severity_br059_3` | `critical` | BR-059-3 接收客户端内容违规严重级别 |
| `session_store_review.severity_br059_4` | `critical` | BR-059-4 未忽略客户端内容违规严重级别 |
| `session_store_review.severity_br059_5` | `suggestion` | BR-059-5 无 TTL 写入违规严重级别 |
| `session_store_review.max_sessions` | `100` | 会话数量上限（超过触发 LRU 淘汰） |
| `session_store_review.ttl_ms` | `3600000` | 会话 TTL（毫秒，默认 1 小时） |
| `session_store_review.trust_client_content` | `false` | 是否信任客户端传的内容字段 |
| `session_store_review.evict_strategy` | `ttl-then-lru` | 淘汰策略（先 TTL 后 LRU） |
| `session_store_review.reference_fields` | `sessionId,messageIndex` | 引用模式接受的字段列表 |

## 检查方式

1. **双层淘汰检查**：用 Grep 检索 `new Map(` 会话存储类，确认 `set()` 方法中有 `evictExpired()` + `while (size > max) Map.delete(Map.keys().next().value)` 逻辑。无淘汰策略 → **BR-059-1 违规**。只按 TTL 淘汰无 LRU → **BR-059-1 违规**。
2. **TTL 检查检查**：用 Grep 检索 `get(` 方法，确认有 `if (Date.now() > s.expiresAt)` 过期检查。未检查 → **BR-059-2 违规**。
3. **引用模式检查**：用 Grep 检索归档/查询接口（`/api/archive` / `/api/query`）的请求体解构，确认只解构 `reference_fields`（sessionId, messageIndex），不解构 `content` / `answer` / `result`。接收内容字段 → **BR-059-3 违规**。
4. **防篡改检查**：`trust_client_content` 为 false 时，用 Grep 检索归档/查询接口函数体，确认未使用客户端传的 `content` / `answer` / `result` 字段。使用了 → **BR-059-4 违规**。
5. **expiresAt 检查**：用 Grep 检索 `set()` 方法，确认有 `session.expiresAt = Date.now() + ttl_ms` 赋值。未设置 → **BR-059-5 违规**（suggestion）。
6. **上限检查**：用 Grep 检索 `max_sessions` 引用，确认 config 中有此字段且值合理（默认 100）。config 缺失 → suggestion。

## 正确示例

```typescript
// services/api/src/services/session-service.ts
import { config } from '../config.js';

const ss = config.session_store_review;

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

class SessionStore {
  private sessions = new Map<string, Session>();

  set(id: string, session: Session): void {
    // ✅ 第一层：TTL 淘汰过期项（BR-059-1）
    this.evictExpired();
    // ✅ 写入时记录 expiresAt（BR-059-5）
    session.expiresAt = Date.now() + ss.ttl_ms;
    this.sessions.set(id, session);
    // ✅ 第二层：LRU 淘汰（BR-059-1）
    while (this.sessions.size > ss.max_sessions) {
      const oldest = this.sessions.keys().next().value;
      if (oldest === undefined) break;
      this.sessions.delete(oldest);
    }
  }

  get(id: string): Session | null {
    const s = this.sessions.get(id);
    if (!s) return null;
    // ✅ 读取时检查 TTL（BR-059-2）
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
// ✅ 归档接口：引用模式，不接收客户端传内容（BR-059-3, BR-059-4）
app.post('/api/archive', async (request, reply) => {
  const { sessionId, messageIndex } = request.body as {
    sessionId: string; messageIndex: number; // ✅ 只接受引用字段
  };
  // ✅ 内容从服务端 sessions 取，客户端无法篡改
  const session = sessionStore.get(sessionId);
  if (!session) return reply.code(404).send({ error: 'session not found' });
  const message = session.messages[messageIndex];
  if (!message) return reply.code(404).send({ error: 'message not found' });
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
// 错误 1：无淘汰策略，内存溢出（BR-059-1 违规）
class SessionStore {
  private sessions = new Map<string, Session>();
  set(id: string, s: Session) {
    this.sessions.set(id, s); // ❌ 无上限，无 TTL
  }
}

// 错误 2：读取时不检查 TTL（BR-059-2 违规）
get(id: string): Session | null {
  return this.sessions.get(id) ?? null; // ❌ 未检查 expiresAt
}

// 错误 3：归档接口接收客户端传的 content（BR-059-3 违规）
app.post('/api/archive', async (request, reply) => {
  const { sessionId, content, outputMode } = request.body; // ❌ 接收 content
  archiveMediaProduct({ prompt: content }); // ❌ 用客户端传的 content
});

// 错误 4：trust_client_content = false 但仍使用 content（BR-059-4 违规）
app.post('/api/archive', async (request, reply) => {
  const { sessionId, messageIndex, content } = request.body; // ❌ 解构了 content
  if (content) { archiveWith(content); } // ❌ 使用了 content
});

// 错误 5：无 TTL 写入（BR-059-5 违规，suggestion）
set(id: string, session: Session) {
  this.sessions.set(id, session); // ❌ 未设置 expiresAt
}
```

## 适配新项目

- **Redis 项目**：`max_sessions` 与 `ttl_ms` 改为 Redis 配置，淘汰策略由 Redis 自管理（`maxmemory-policy: allkeys-lru`）
- **数据库持久化项目**：会话写入数据库，TTL 用 `expire_at` 字段查询过滤，无需内存淘汰
- **无状态服务项目**：会话存到 JWT 或客户端 cookie（签名防篡改），服务端不存会话
- **高并发项目**：用 LRU cache 库（如 `lru-cache` npm 包）替代手写 Map，线程安全且性能更优
- **长会话场景项目**：`ttl_ms` 调大到 24 小时或更长，`max_sessions` 按用户数估算

## 与其他规则的关系

- 与 BR-058（媒体归档 frontmatter）联动：归档接口用本规则的引用模式取内容，再用 BR-058 的 frontmatter 标准归档
- 与 BR-057（长/短任务架构分离）联动：长任务进行中的中间状态存入会话，任务完成后归档
- 与 BR-037（跨 origin 持久化边界）联动：会话类数据权威源为后端，浏览器存储仅作降级缓存
- 与 session-state 规则联动：本规则关注内存 Map 淘汰策略，session-state 关注跨进程状态同步
- 与 CODING-061（会话存储双层淘汰）对应：本规则是 CODING-061 的后端审查视角
