# 前端多账户会话状态隔离规则

**代码**：CODING-SESSION-ISOLATION
**严重级别**：critical

## 问题（Problem）

会话仅存客户端（IndexedDB，按 `ownerId` 隔离，不落服务端）。但 **Pinia 模块级共享的会话状态 ref（如 `currentConversationId`）** 在账户切换 / 登出时若未被重置，下一账户复用同一 id 去调用持久化（`persistConversation`），会把上一账户**相同 id** 的会话覆盖并改属自己——表现为「admin 历史消失 / 人人可见」。这类跨账户泄漏极难排查，因为单账户测试永远复现不出。

我们曾因此反复出现"问题依然存在"的误判：E2E 用 store 直接 `setUser` 不会触发**真实登出**流程，从而漏掉 `resetSession` 缺失这个真正的根因；而真正根因是模块级共享 ref 在跨账户时未失效。

> 另一真实踩坑：`scopedOwnerId` ref 最初**漏加到 store 的 return 对象**，导致 `resetSession` 里对它的赋值不可观测（等于死状态），重置形同虚设。Pinia setup store 的 state 仅含 return 中的 ref，漏加即失效。

## 规则（Rule）

### R-1：账户切换 / 登出必须 reset 会话状态（reset-on-auth-change）

跨账户前必须让模块级会话状态失效。store 暴露 `resetSession()`（作废 `currentConversationId` + `scopedOwnerId` + 清空列表）；消费侧（如问答页）的 auth watch（监听 `user?.id` 变化）必须**先调 `resetSession()` 再 `loadConversations()`**。

```typescript
// stores/conversations.ts（setup store 必须显式 return 所有会话状态 ref）
export const useConversationsStore = defineStore('conversations', () => {
  const currentConversationId = ref<string | null>(null);
  const scopedOwnerId = ref<string | null>(null);   // ← 必须加入 return，否则 reset 赋值不可观测
  const list = ref<Conversation[]>([]);

  function resetSession() {
    currentConversationId.value = null;
    scopedOwnerId.value = null;
    list.value = [];
  }
  // ...其余 action
  return { currentConversationId, scopedOwnerId, list, resetSession, /* ... */ };
});

// views/Query.vue — auth watch 先 reset 再 load
watch(() => authStore.user?.id, (id, prev) => {
  if (id !== prev) {
    store.resetSession();      // 关键：跨账户前失效旧会话状态
    store.loadConversations();
  }
});
```

### R-2：复用 id 持久化前必须以存储实际记录校验归属

`persistConversation` 复用一个已存在的会话 id 时，必须先用存储实际记录（IndexedDB `dbGet`）校验归属：**已存在且归属他人 → 改用全新 `uuid`，绝不复用他人 id、绝不覆盖/改属他人记录**。归属迁移（如 `migrateOwnerless`）须「落盘成功后才内存归属」（安全失败不泄漏）。

```typescript
async function persistConversation(conv: Conversation) {
  const existing = await dbGet(conv.id);            // 以存储实际记录为准
  if (existing && existing.ownerId && existing.ownerId !== conv.ownerId) {
    conv.id = uuid();                                // 冲突 → 全新 id，绝不覆盖他人
  }
  await dbPut(conv);                                 // 先落盘
  // migrateOwnerless 等：必须 dbPut 成功后才更新内存 owner，安全失败不泄漏
}
```

### R-3：严格按 ownerId 隔离 + 二次防御

`filterByOwner` 保持严格：已登录 `ownerId === owner`，未登录返回空。并在 `loadConversations` 内做二次防御——若本次 owner 与 `scopedOwnerId` 不同，重置 `currentConversationId`，阻断任何复用上一账户 id 的路径。

## 适用 / 不适用

- **适用**：客户端按用户隔离的会话 / 草稿 / 个人配置（IndexedDB / localStorage），且状态以 Pinia 模块级 ref 持有；涉及账户切换 / 登出 / 多账户并存的场景；CI 跨账户回归门禁。
- **不适用**：纯服务端会话（服务端按 token/session 自然隔离，无模块级共享 ref 问题）、单账户应用、与认证无关的纯展示组件。

## 检查清单

- [ ] 会话状态 ref（`session_isolation.state_refs_must_return` 列出的 `currentConversationId` / `scopedOwnerId` 等）是否全部出现在 store 的 return 对象中（用 grep 核对，漏加即死状态）
- [ ] auth watch（`session_isolation.reset_on_auth_signal` 如 `user?.id`）是否在跨账户时先调 `resetSession()` 再 `loadConversations()`
- [ ] `persistConversation` 复用 id 前是否以存储实际记录（`session_isolation.owner_check_source`，如 IndexedDB `dbGet`）校验归属，冲突时改用全新 uuid
- [ ] `filterByOwner` 是否严格按 `ownerId` 隔离（未登录返回空）
- [ ] 归属迁移（如 `migrateOwnerless`）是否「落盘成功后才内存归属」
- [ ] 是否有跨账户 E2E（真实登出/切换，而非 store 直接 `setUser`）验证无泄漏
