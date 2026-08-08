# 流式回答增量持久化与断点续答规则

**代码**：CODING-STREAMING-RESUME
**严重级别**：critical

## 问题（Problem）

知识库问答页的 AI 回答是流式输出（SSE / token 流）。早期实现把**部分答案仅存内存** `streamingAnswer`，`persistConversation` 仅在回答「完成 / 用户停止」后才落盘。后果：① 流式过程中「切换页面」或「刷新页面」，问答状态完全丢失——刷新变成一个**新问题（新会话）**、部分答案消失；② `onBeforeUnmount` 调 `abortController?.abort()` 在切页时直接杀掉 SSE → 回答死状态；③ 无「上次活跃会话」记忆，重载无法判定续答。这类「流式中间态丢失」在单轮测试中不易暴露，却是真实用户高频操作（切走看别的、回来发现回答没了）。

## 规则（Rule）

### R-1：流式 / 部分答案状态须增量持久化（防抖），而非仅在完成时落盘

流式每收到分片，须**防抖落盘中间态**（如 1.5s 防抖），把「问题 + 部分答案 + 状态=streaming」写入客户端持久层。这样刷新 / 切页回来时，进行中的问题与已生成的部分答案都可恢复，而不是退化为全新空会话。

```typescript
// stores/query.ts — 流式每收分片防抖落盘
watch(streamingAnswer, () => schedulePersistInProgress()); // 防抖 1.5s
function schedulePersistInProgress() {
  clearTimeout(persistTimer);
  persistTimer = setTimeout(() => persistConversation(partialConv('streaming')), 1500);
}
```

### R-2：页面切换 / 组件卸载不得 abort 在途流（后台继续生成）

`onBeforeUnmount` **只能卸载事件监听**，绝不能 `abortController?.abort()`——否则切页即杀 SSE，后台回答中断。切页后 SSE 应继续在后台生成，用户回来时答案已补全。

```typescript
onBeforeUnmount(() => {
  // 仅卸载监听器，绝不 abortController?.abort() —— 切页不中断流
  window.removeEventListener('pagehide', onPageHide);
});
```

### R-3：加载时恢复——检测 streaming 末条自动续答，interrupted/error 不自动续

重载时若有「上次活跃会话」且末条为 `status:'streaming'`，则**续答**（移除占位 + 复用末条用户问题重发补全；真·断点续写不可行时采用「重新生成完整回答」替换占位）。`status` 为 `interrupted` / `error` 的**不自动续**（保留部分答案，交用户决定）。若 SPA 重挂载时 store 仍 `isLoading`（后台流活跃），直接跳过，避免打断 / 重复续答。

```typescript
async function maybeResumeOnLoad() {
  const last = getLastActiveConversation();
  const tail = last?.messages.at(-1);
  if (tail?.status === 'streaming') await resumeLastAnswer(); // 重生成完整回答替换占位
  // interrupted / error 不自动续，保留部分答案
}
```

## 适用 / 不适用

- **适用**：任何 SSE / 流式输出 UI（聊天、问答、长文生成）；客户端持久化会话 / 草稿；用户会中途切页或刷新的场景；刷新 / 断网恢复门禁。
- **不适用**：纯一次性请求（无中间态）、服务端已完整托管会话且前端只做展示、不持久化流式中间态的只读展示页。

## 检查清单

- [ ] 流式分片是否**增量（防抖）落盘**中间态（`streaming_resume.persist_debounce_ms`），而非仅完成时落盘
- [ ] `onBeforeUnmount` 是否**仅卸载监听、不 abort 在途流**（`streaming_resume.no_abort_on_unmount`）
- [ ] 是否有「上次活跃会话」记忆并在重载时恢复（`streaming_resume.last_active_key`）
- [ ] 续答是否只对 `status:'streaming'` 末条触发，`interrupted` / `error` 不自动续（`streaming_resume.resume_only_streaming`）
- [ ] SPA 重挂载且后台流仍活跃（`isLoading`）时是否跳过续答，避免打断 / 重复
