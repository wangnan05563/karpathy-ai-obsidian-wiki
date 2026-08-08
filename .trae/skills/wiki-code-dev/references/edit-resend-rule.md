# 编辑重发：丢弃尾部后必须重新插入用户消息

**代码**：CODING-EDIT-RESEND
**严重级别**：critical

## 问题（Problem）

问答 / 聊天页支持「编辑已发送的用户消息并重新发送」（编辑重发）。其正确时序是：① 终止当前正在生成的 AI 回复（若流式进行中）→ ② 丢弃被编辑的 user 消息及其之后的所有消息 → ③ 把编辑后的 user 消息**重新插入**对话 → ④ 重新触发生成。

陷阱在于第 ② 步与第 ③ 步必须成对出现：`removeMessagesFrom(i)` 会从索引 i 起丢弃（含被编辑的 user 消息本身）。若只调用 `removeMessagesFrom` 而**未**用 `submitQuestion` 重新插入编辑后的 user 消息，对话里就只剩「悬空的 AI 答案」——用户问题凭空消失，上下文断裂，且后续续答/持久化全部基于错误的前提。此缺陷在「首问」单测中不会暴露（首问走 `submitQuestion` 不经 `removeMessagesFrom`），只在「编辑重发」路径触发。

> 真实代码佐证（`frontend/src/views/Query.vue:652-654`）：`store.removeMessagesFrom(i);` 后紧跟注释「被编辑的 user 消息已被 removeMessagesFrom 丢弃，必须 submitQuestion 重新插入，否则对话里只剩悬空答案」。

## 规则（Rule）

### R-1：编辑重发必须先 `removeMessagesFrom` 再 `submitQuestion` 重新插入

编辑重发的核心不变量：`removeMessagesFrom(i)` 丢弃尾部后，必须立即以编辑后的文本调用 `submitQuestion(q)` 重新插入 user 消息，二者在同一处理函数内、不可拆分。任何「只丢弃不重插」或「重插到错误位置」的实现都破坏对话完整性。

```typescript
// views/Query.vue — handleConfirmEdit
const i = originalIndex;            // 被编辑 user 消息的索引
store.removeMessagesFrom(i);        // 丢弃被编辑 user 消息及其之后全部
store.submitQuestion(editedText);   // 必须重新插入，否则只剩悬空答案
```

### R-2：编辑重发须先终止在途回复，再丢弃尾部

若当前正在流式生成，编辑重发前必须走「edit」停止路径（仅清空本轮 + 解除 loading，不追加 `[已停止]`、不弹提示），待 `isLoading` 释放后再 `removeMessagesFrom`。否则旧流与新重发会并发写入同一会话，产生重复 / 交错答案。

### R-3：未修改文本时退出编辑态、不重发（幂等）

若编辑后文本 `trim()` 与原内容相等，直接 `editingIdx = null` 退出编辑态，**不**触发 `removeMessagesFrom` / `submitQuestion`，避免无谓的会话重写与答案丢失。

## 适用 / 不适用

- **适用**：允许编辑已发送消息并重新生成的聊天 / 问答 UI；消息以数组索引定位、删除尾部后需重建的场景；流式生成与编辑操作可能并发的界面。
- **不适用**：只读展示页；追加式日志（不可修改历史）；每条消息独立不可变的审计流；首问路径（不经 `removeMessagesFrom`）。

## 检查清单

- [ ] 编辑重发处理函数内，`removeMessagesFrom(i)` 后是否**紧跟** `submitQuestion(编辑后文本)` 重新插入（`edit_resend.reinsert_required`）
- [ ] 编辑重发前是否先终止在途流式回复、释放 `isLoading`，再丢弃尾部（`edit_resend.stop_inflight_first`）
- [ ] 编辑后文本未变化时是否**不**重发、仅退出编辑态（`edit_resend.idempotent_noop`）
- [ ] 丢弃尾部后，被编辑的 user 消息是否在对话中重新可见（无悬空 AI 答案）
- [ ] 重发是否复用「末条用户问题重发」语义，而非新建一个不同会话
