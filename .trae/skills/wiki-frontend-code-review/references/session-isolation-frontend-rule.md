# Rule Catalog — Session Cross-Account Isolation (Pinia)

前端多账户会话隔离审查规则：确保客户端按用户隔离的会话状态在账户切换/登出时真正失效、Pinia setup store 的会话 state ref 可被观测、持久化复用 id 前校验归属，防止跨账户会话泄漏（表现为「历史消失 / 人人可见」）。所有参数从 `config/review-config.md` 读取，禁止在规则文件中硬编码。

> 复盘来源：会话仅存客户端 IndexedDB（按 `ownerId` 隔离，不落服务端）。`currentConversationId` 是 Pinia 模块级共享 ref，账户切换/登出若未重置，下一账户复用同一 id 调 `persistConversation` 会把上一账户的会话（相同 id）覆盖并改属自己。真实踩坑还包括 `scopedOwnerId` ref 漏加到 store 的 return 对象 → `resetSession` 赋值不可观测=死状态；以及 E2E 用 store 直接 `setUser` 不触发真实登出，从而漏掉根因。

## Scope
- Covers: `frontend/src/stores/**/*store*.ts`（会话 state ref 与 return）、`frontend/src/views/**/*.vue`（auth watch 与 reset 调用）、`frontend/src/**/chatDb.ts` 或会话持久化层（`persistConversation` / `dbGet` / `dbPut` / `filterByOwner` / `migrateOwnerless`）。
- Does NOT cover: 纯服务端会话（按 token 自然隔离）、与认证无关的纯展示组件、单账户应用。

## Rules

### FR-069-1: Pinia setup store 的会话状态 ref 必须加入 return 对象

IsUrgent: True
Category: Session Isolation

#### Description

Pinia setup store 的 state 仅包含 return 中出现的 ref。会话状态 ref（`session_isolation_frontend.session_state_refs` 列出的 `currentConversationId` / `scopedOwnerId` 等）**必须全部出现在 store 的 return 对象中**。若漏加，`resetSession()` 内对这些 ref 的赋值不可观测（`store.xxx` 读不到、写不进去），重置形同虚设，跨账户泄漏防护直接失效。

#### Suggested Fix

```typescript
export const useConversationsStore = defineStore('conversations', () => {
  const currentConversationId = ref<string | null>(null);
  const scopedOwnerId = ref<string | null>(null);
  const list = ref<Conversation[]>([]);
  function resetSession() {
    currentConversationId.value = null;
    scopedOwnerId.value = null;
    list.value = [];
  }
  return { currentConversationId, scopedOwnerId, list, resetSession, /* 其余 action */ };
  //                                                                  ↑ 会话状态 ref 必须在此列出，否则 reset 不可观测
});
```

> **示例代码**: 见 config-isolation-rule.md（多实例配置命名空间隔离）与 runtime-data-privacy-frontend-rule.md（FR-063，客户端持久化按 ownerId）。

### FR-069-2: 账户切换 / 登出必须 resetSession（先 reset 再 load）

IsUrgent: True
Category: Session Isolation

#### Description

跨账户前必须让模块级会话状态失效。store 须暴露 `resetSession()`（作废 `currentConversationId` + `scopedOwnerId` + 清空列表）；消费侧（如问答页）的 auth watch（监听 `session_isolation_frontend.auth_watch_signal` 如 `user?.id` 变化）必须**先调 `resetSession()` 再 `loadConversations()`**。仅 `loadConversations` 不带 reset，会复用上一账户残留的 `currentConversationId` 去持久化，造成覆盖/改属。

> 注意：E2E 不能用 store 直接 `setUser` 模拟切换（不触发真实登出），必须用真实登出/登录流程才能验证根因是否修复。

#### Suggested Fix

```typescript
watch(() => authStore.user?.id, (id, prev) => {
  if (id !== prev) {
    store.resetSession();      // 先失效旧会话状态
    store.loadConversations(); // 再加载当前账户
  }
});
```

> **示例代码**: 见 runtime-data-privacy-frontend-rule.md（FR-063，会话默认客户端存储）。

### FR-069-3: persistConversation 复用 id 前必须以实际记录校验归属

IsUrgent: True
Category: Session Isolation

#### Description

`persistConversation` 复用已存在会话 id 时，必须以存储实际记录（`session_isolation_frontend.owner_store` 如 IndexedDB `dbGet`）校验归属：**已存在且归属他人 → 改用全新 `uuid`，绝不复用他人 id、绝不覆盖/改属他人记录**。仅凭内存 `currentConversationId` 判断会误判归属（残留上一账户的 id），是跨账户泄漏的直接成因。

#### Suggested Fix

```typescript
async function persistConversation(conv: Conversation) {
  const existing = await dbGet(conv.id);            // 以存储实际记录为准
  if (existing && existing.ownerId && existing.ownerId !== conv.ownerId) {
    conv.id = uuid();                                // 冲突 → 全新 id，绝不覆盖他人
  }
  await dbPut(conv);
}
```

> **示例代码**: 见 persistence-boundary-rule.md（PB1-PB6，客户端持久化边界）与 runtime-data-privacy-frontend-rule.md（FR-063）。

### FR-069-4: 二次防御 + 严格隔离 + 落盘后归属

IsUrgent: False
Category: Session Isolation

#### Description

纵深防御（suggestion 级，但强烈建议）：
- `loadConversations` 内：若本次 owner 与 `scopedOwnerId` 不同，重置 `currentConversationId`（二次防御）。
- `filterByOwner` 保持严格：已登录 `ownerId === owner`，未登录返回空。
- 归属迁移（如 `migrateOwnerless`）须「落盘成功后才内存归属」（安全失败不泄漏）。

#### Suggested Fix

```typescript
async function loadConversations() {
  if (scopedOwnerId.value && currentOwnerId !== scopedOwnerId.value) {
    currentConversationId.value = null; // 二次防御：owner 不符则作废当前会话
  }
  // ...
}
// migrateOwnerless：dbPut 成功后才更新内存 owner，失败则保持无归属（不泄漏）
```

> **示例代码**: 见 runtime-data-privacy-frontend-rule.md（FR-063，按 ownerId 隔离客户端数据）。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `session_isolation_frontend.enabled` | `true` | 启用本组规则（FR-069） |
| `session_isolation_frontend.severity_return_ref` | `critical` | FR-069-1 会话状态 ref 漏加 return 违规级别 |
| `session_isolation_frontend.severity_reset_on_auth` | `critical` | FR-069-2 账户切换/登出未 resetSession 违规级别 |
| `session_isolation_frontend.severity_persist_owner_check` | `critical` | FR-069-3 复用 id 未校验归属违规级别 |
| `session_isolation_frontend.severity_defense_in_depth` | `suggestion` | FR-069-4 二次防御/严格隔离/落盘后归属违规级别 |
| `session_isolation_frontend.session_state_refs` | `currentConversationId,scopedOwnerId` | 须加入 store return 的会话状态 ref |
| `session_isolation_frontend.auth_watch_signal` | `user?.id` | auth watch 信号（变化即跨账户） |
| `session_isolation_frontend.owner_store` | `chatDb (IndexedDB)` | 会话隔离存储（按 ownerId） |
