# Rule Catalog — Streaming Answer Incremental Persistence & Resume (Frontend)

前端流式回答增量持久化与断点续答审查规则：确保 SSE / token 流的部分答案增量落盘（而非仅完成时）、页面切换 / 卸载不中断在途流、重载时按「上次活跃会话 + streaming 末条」自动续答（`interrupted` / `error` 不自动续）。所有参数从 `config/review-config.md` 读取，禁止在规则文件中硬编码。

> 复盘来源：问答页 AI 回答早期仅内存持有 `streamingAnswer`、`persistConversation` 仅完成时落盘；`onBeforeUnmount` 调 `abortController?.abort()` 在切页杀 SSE。后果：刷新 → 新问题（新会话）且部分答案消失；切页 → 回答死状态；无「上次活跃会话」记忆无法续答。修复为流式分片防抖落盘 + 卸载仅卸监听不 abort + 重载恢复 streaming 末条续答。

## Scope
- Covers: `frontend/src/stores/**/query.ts`（streamingAnswer 落盘 / resume）、`frontend/src/views/**/Query.vue`（onBeforeUnmount / onMounted resume / pagehide）、`frontend/src/constants/storageKeys.ts`（last-active key）、`frontend/src/types.ts`（ChatMessage.status）。
- Does NOT cover: 纯一次性请求无中间态、服务端完整托管会话的只读展示页、不持久化流式中间态的页面。

## Rules

### FR-071-1: 流式分片增量（防抖）落盘，而非仅完成时

IsUrgent: True
Category: Streaming Resume

#### Description

`streamingAnswer` 每收到分片须**防抖落盘**中间态（如 `streaming_resume.persist_debounce_ms` 配置的 1.5s），把「问题 + 部分答案 + status:'streaming'」写入客户端持久层。仅完成时落盘会导致刷新 / 切页后退化为全新空会话、部分答案丢失。

#### Suggested Fix

```typescript
watch(streamingAnswer, () => schedulePersistInProgress());
function schedulePersistInProgress() {
  clearTimeout(persistTimer);
  persistTimer = setTimeout(() => persistConversation(partialConv('streaming')), 1500);
}
```

> **示例代码**: 见 persistence-boundary-rule.md（PB1-PB6，客户端持久化边界）与 session-isolation-frontend-rule.md（FR-069，客户端按 ownerId 持久化）。

### FR-071-2: 卸载 / 切页不得 abort 在途流

IsUrgent: True
Category: Streaming Resume

#### Description

`onBeforeUnmount` **只能卸载事件监听**，绝不能 `abortController?.abort()`——否则切页即杀 SSE，后台回答中断成死状态。流式应在后台继续生成，用户回来时答案已补全。

#### Suggested Fix

```typescript
onBeforeUnmount(() => {
  window.removeEventListener('pagehide', onPageHide); // 仅卸监听
  // 严禁 abortController?.abort() —— 切页不中断流
});
```

> **示例代码**: 见 sse-event-dispatch-frontend-rule.md（SSE 事件分发）与 sse-stream-error-frontend-rule.md（流消费错误处理）。

### FR-071-3: 重载恢复——仅 streaming 末条续答，interrupted/error 不自动续

IsUrgent: True
Category: Streaming Resume

#### Description

重载时若有「上次活跃会话」且末条为 `status:'streaming'`，则**续答**（移除占位 + 复用末条用户问题重发补全；真·断点续写不可行时采用「重新生成完整回答」替换占位）。`status` 为 `interrupted` / `error` 的**不自动续**（保留部分答案）。若 SPA 重挂载时 store 仍 `isLoading`（后台流活跃），直接跳过，避免打断 / 重复续答。

#### Suggested Fix

```typescript
async function maybeResumeOnLoad() {
  const tail = getLastActiveConversation()?.messages.at(-1);
  if (tail?.status === 'streaming') await resumeLastAnswer(); // 重生成完整回答替换占位
  // interrupted / error 不自动续，保留部分答案
}
```

> **示例代码**: 见 persistence-boundary-rule.md（PB1-PB6）与 session-isolation-frontend-rule.md（FR-069）。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `streaming_resume_frontend.enabled` | `true` | 启用本组规则（FR-071） |
| `streaming_resume_frontend.severity_incremental_persist` | `critical` | FR-071-1 仅完成时落盘、未增量防抖落盘违规级别 |
| `streaming_resume_frontend.severity_no_abort_on_unmount` | `critical` | FR-071-2 卸载/切页 abort 在途流违规级别 |
| `streaming_resume_frontend.severity_resume_gate` | `critical` | FR-071-3 续答门禁（仅 streaming 续、interrupted/error 不续）违规级别 |
| `streaming_resume_frontend.persist_debounce_ms` | `1500` | 流式分片增量落盘防抖毫秒 |
| `streaming_resume_frontend.last_active_key` | `LAST_ACTIVE_CONVERSATION` | 上次活跃会话存储键 |
| `streaming_resume_frontend.streaming_status` | `streaming` | 触发续答的会话末条状态 |
| `streaming_resume_frontend.skip_when_loading` | `true` | SPA 重挂载且后台流活跃(isLoading)时跳过续答 |
