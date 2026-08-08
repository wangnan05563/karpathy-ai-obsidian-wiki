# 消息气泡进入编辑态须撑满问答列宽

**代码**：CODING-EDITBOX-WIDTH
**严重级别**：minor

## 问题（Problem）

聊天 / 问答页中，已发送的 user 消息气泡通常右对齐、且限制最大宽度（如 `max-width: 75%`）以区分 AI 回复。当该气泡切换为「可编辑态」（textarea 替换原文本）时，若编辑器直接继承气泡的窄宽度与右对齐，编辑框会显得局促、文字频繁换行，体验远差于首问输入框。

> 真实代码佐证（`frontend/src/views/Query.vue`）：`.msg-content-wrapper.editing` 用 `align-items: stretch` 抵消 `.msg-content-wrapper.user` 的 `flex-end`，使内层气泡撑满整列宽度；`.msg-edit` 设 `width: 100%` 自动跟随撑满。注释明确「align-items:stretch 抵消 .msg-content-wrapper.user 的 flex-end，让内层气泡撑满宽度；.msg-edit 已是 width:100% 自动跟随撑满」。

## 规则（Rule）

### R-1：进入编辑态的编辑器容器须撑满问答列宽

当消息气泡进入可编辑态，其编辑容器（textarea / input 外层）必须扩展为**填满整个问答列宽度**，不可停留在已发送气泡的窄宽度（右对齐 + 受限 max-width）下。

```css
.msg-content-wrapper.editing { align-items: stretch; } /* 抵消 .user 的 flex-end，撑满整列 */
.msg-edit { width: 100%; }                               /* 编辑框跟随撑满 */
```

### R-2：用 `align-items: stretch` / `width:100%` 覆盖已发送态的对齐

已发送 user 气泡多用 `flex-end` 右对齐 + `max-width`，编辑态须显式以 `align-items: stretch`（或等价）覆盖该对齐，并令编辑器 `width: 100%`，使编辑区域与首问输入框视觉一致。

### R-3：textarea / input 须 `width:100%` 充满编辑容器

编辑控件自身 `width: 100%`，且其内边距（padding）应适当放宽（如从 2px 增至 10px 12px），避免文字贴边、提升输入舒适度（与首问输入框体验对齐）。

## 适用 / 不适用

- **适用**：聊天 / 问答页中「内联编辑已发送消息」的场景；已发送气泡与编辑框同处一个对齐容器、需切换宽度的 UI。
- **不适用**：独立的全宽编辑页 / 独立编辑弹窗（本身即全宽，不存在气泡窄宽继承问题）；不可编辑的消息展示。

## 检查清单

- [ ] 消息进入编辑态时，编辑容器是否撑满问答列宽而非停留在已发送气泡窄宽（`editbox_width.fill_column`）
- [ ] 是否以 `align-items: stretch` / `width:100%` 覆盖已发送态 `flex-end` 对齐（`editbox_width.override_alignment`）
- [ ] textarea / input 是否 `width:100%` 且内边距与首问输入框一致（`editbox_width.control_fullwidth`）
