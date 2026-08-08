# CODING-PERSISTENCE-CLIENT-CONTENT-DECOUPLING — 持久化内容与服务端会话解耦

> 来源：归档路由原本依赖服务端 `ThreadMemoryStore.getSession(threadId)` 取 Q&A 内容。但项目核心需求"会话不存服务端、仅本地 IndexedDB 维护"（`threadsPersist=false` 默认）→ 磁盘无 session.json → `getSession` 永远 null → 归档 100% 返回"会话或消息不存在（可能已清理）" → 前端误报"该问答已过期"。修复：改为从请求体取内容，与"服务端不落盘会话"政策一致。
> 对应审查规则：后端 BR-086 / 前端 FR-076。

## 触发关键词

`getSession` / `ThreadMemoryStore` / `threadsPersist` / 归档 / 内容从请求体 / `archive` / 服务端会话 / 过期误报 / 本地 IndexedDB

## 严重级别

🔴 Critical（UX 漏洞：默认部署下功能 100% 失败，且文案误导）

## 规则

- **PCC-1**：持久化/归档用户生成内容时，**优先从请求体取内容**（前端已持有 `question`/`answer`/`refs` 等），而非重新从服务端会话状态取——尤其当服务端会话持久化按政策默认关闭（`server_side_sessions=false`，对应 BR-065 / runtime-data-privacy）时，服务端无会话可读。
- **PCC-2**：仅当请求体内容缺失（向后兼容旧客户端 / `threadsPersist=true` 部署）才回退 `getSession` 取数；回退路径须校验 record 存在，缺失返回 404（明确"会话不存在"）而非 500。
- **PCC-3**：该解耦须与前端同步——前端 `:can-archive` 等门控不再要求 `sessionId`（内容自请求体带），避免功能被静默禁用（见 CODING-CAPABILITY-GATING-SYNC / FR-076）。
- **PCC-4**：**不擅自开启 `threadsPersist=true`** 来"修复"——违背多用户数据隔离核心需求；正确做法是 PCC-1 解耦。

## 正 / 误示例

```ts
// ❌ 误：默认无服务端会话 → getSession 永 null → 100% 归档失败
const record = store.getSession(threadId)?.messages[messageIndex];
if (!record) return reply.code(404).send({ error: '会话或消息不存在（可能已清理）' });

// ✅ 正：优先请求体内容，仅缺失时回退服务端（兼容旧客户端）
let { question, answer, refs } = body;
if (!answer) {
  const record = store.getSession(threadId)?.messages[messageIndex];
  if (!record) return reply.code(404).send({ error: '会话或消息不存在（可能已清理）' });
  question ??= record.question; answer ??= record.answer; refs ??= record.refs;
}
```

## 检查清单

- [ ] 归档/持久化路由是否依赖服务端会话？默认无会话部署下是否仍可用？
- [ ] 是否优先请求体内容、仅缺失时回退（而非反之）？
- [ ] 前端对应门控是否同步放宽（不再要求 sessionId）？
- [ ] 是否通过"开 threadsPersist"绕过（违背隔离需求）？
