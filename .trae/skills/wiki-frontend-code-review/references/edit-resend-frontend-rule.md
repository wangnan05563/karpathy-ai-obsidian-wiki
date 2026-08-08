# Rule Catalog — Edit & Resend Re-inserts User Message (Frontend)

前端「编辑已发送消息并重新发送」（编辑重发）审查规则：确保 `removeMessagesFrom(i)` 丢弃尾部后必须 `submitQuestion` 重新插入编辑后的 user 消息，否则对话只剩悬空 AI 答案；重发前须先终止在途流式回复；文本未变仅退出编辑态不重发。所有参数从 `config/review-config.md` 读取，禁止在规则文件中硬编码。

> 复盘来源：问答页编辑重发早期仅调 `removeMessagesFrom(i)` 丢弃被编辑 user 消息及其后续，却未重新插入 → 对话里只剩 AI 答案、用户问题凭空消失、上下文断裂。首问路径不经 `removeMessagesFrom` 故单测不暴露，仅在编辑重发路径触发。`Query.vue:652-654` 注释明确「被编辑的 user 消息已被 removeMessagesFrom 丢弃，必须 submitQuestion 重新插入，否则对话里只剩悬空答案」。

## Scope
- Covers: `frontend/src/views/**/Query.vue`（handleConfirmEdit / removeMessagesFrom / submitQuestion / editingIdx）、`frontend/src/stores/**/query.ts`（removeMessagesFrom / submitQuestion / isLoading）、`frontend/src/components/**/MessageToolbar.vue`（编辑并重发入口）。
- Does NOT cover：只读展示页；追加式日志（不可修改历史）；不可变审计流；首问路径（不经 removeMessagesFrom）。

## Rules

### FR-077-1: 编辑重发须 `removeMessagesFrom(i)` 后紧跟 `submitQuestion` 重插

IsUrgent: True
Category: Edit Resend

#### Description

编辑重发的核心不变量：`removeMessagesFrom(i)` 丢弃被编辑 user 消息及其之后全部后，必须**同一处理函数内**立即以编辑后文本 `submitQuestion(q)` 重新插入。任何「只丢弃不重插」或「重插到错误位置」都破坏对话完整性，产生悬空 AI 答案。

#### Suggested Fix

```typescript
// views/Query.vue — handleConfirmEdit
store.removeMessagesFrom(i);   // 丢弃被编辑 user 消息及其之后全部
store.submitQuestion(editedText); // 必须重新插入，否则只剩悬空答案
```

### FR-077-2: 编辑重发前先终止在途流式回复

IsUrgent: True
Category: Edit Resend

#### Description

若当前 `isLoading`（流式生成中），编辑重发前必须走「edit」停止路径（仅清空本轮 + 解除 loading，不追加 `[已停止]`、不弹提示），待 `isLoading` 释放后再 `removeMessagesFrom`。否则旧流与新重发并发写入同一会话，产生重复 / 交错答案。

### FR-077-3: 文本未变仅退出编辑态、不重发（幂等）

IsUrgent: False
Category: Edit Resend

#### Description

若编辑后文本 `trim()` 与原内容相等，直接 `editingIdx = null` 退出编辑态，**不**触发 `removeMessagesFrom` / `submitQuestion`，避免无谓会话重写与答案丢失。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `edit_resend_frontend.enabled` | `true` | 启用本组规则（FR-077） |
| `edit_resend_frontend.severity_reinsert` | `critical` | FR-077-1 丢弃尾部未重插、产生悬空答案的违规级别 |
| `edit_resend_frontend.severity_stop_inflight` | `critical` | FR-077-2 未先终止在途流导致并发写入的违规级别 |
| `edit_resend_frontend.severity_idempotent` | `minor` | FR-077-3 未做幂等判定、无谓重发的违规级别 |
| `edit_resend_frontend.reinsert_call` | `submitQuestion` | 重插所用方法名（从 store 读取） |
| `edit_resend_frontend.discard_call` | `removeMessagesFrom` | 丢弃尾部所用方法名 |
| `edit_resend_frontend.edit_state_ref` | `editingIdx` | 编辑态索引 ref 名 |
