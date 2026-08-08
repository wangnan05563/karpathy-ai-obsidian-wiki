# Rule Catalog — Edit-State Fills Q&A Column Width (Frontend)

前端「消息进入编辑态须撑满问答列宽」审查规则：已发送 user 消息气泡通常右对齐且受限 max-width，当切换为可编辑态（textarea 替换原文本）时，编辑容器必须撑满整个问答列宽、不可停留在已发送气泡窄宽下。所有参数从 `config/review-config.md` 读取，禁止硬编码。

> 复盘来源：编辑重发时编辑框直接继承 user 气泡的 `flex-end` + `max-width:75%` 窄宽，文字频繁换行、体验远差于首问输入框。`Query.vue` `.msg-content-wrapper.editing` 用 `align-items: stretch` 抵消 `.msg-content-wrapper.user` 的 `flex-end`、`.msg-edit` 设 `width:100%` 撑满；注释明确「align-items:stretch 抵消 .msg-content-wrapper.user 的 flex-end，让内层气泡撑满宽度；.msg-edit 已是 width:100% 自动跟随撑满」。

## Scope
- Covers: `frontend/src/views/**/Query.vue` / `frontend/src/components/**/*.vue`（消息气泡编辑态模板与样式：`.msg-content-wrapper.editing` / `.msg-edit` / `textarea` / `el-input`）、相关 `<style>` 块。
- Does NOT cover：独立全宽编辑页 / 独立编辑弹窗（本身即全宽，不存在窄宽继承）；不可编辑的消息展示。

## Rules

### FR-080-1: 编辑容器须撑满问答列宽

IsUrgent: False
Category: Editbox Width

#### Description

消息气泡进入可编辑态，其编辑容器（textarea / input 外层）必须扩展为**填满整个问答列宽度**，不可停留在已发送气泡的窄宽度（右对齐 + 受限 max-width）下（FR-080-1，建议级）。

### FR-080-2: 以 align-items:stretch / width:100% 覆盖已发送态对齐

IsUrgent: False
Category: Editbox Width

#### Description

已发送 user 气泡多用 `flex-end` 右对齐 + `max-width`，编辑态须显式以 `align-items: stretch`（或等价）覆盖该对齐，并令编辑器 `width: 100%`，使编辑区域与首问输入框视觉一致（FR-080-2，建议级）。

### FR-080-3: textarea/input 须 width:100% 且内边距与首问一致

IsUrgent: False
Category: Editbox Width

#### Description

编辑控件自身 `width: 100%`，且其内边距应适当放宽（如从 2px 增至 10px 12px），避免文字贴边、输入更舒适，与首问输入框体验对齐（FR-080-3，建议级）。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `editbox_width_frontend.enabled` | `true` | 启用本组规则（FR-080） |
| `editbox_width_frontend.severity_fill_column` | `minor` | FR-080-1 编辑容器停留窄宽的违规级别 |
| `editbox_width_frontend.severity_override_alignment` | `minor` | FR-080-2 未覆盖 flex-end 对齐的违规级别 |
| `editbox_width_frontend.severity_control_fullwidth` | `minor` | FR-080-3 控件未 width:100% / 内边距不一致的违规级别 |
| `editbox_width_frontend.editing_wrapper_selector` | `.msg-content-wrapper.editing` | 编辑态容器选择器 |
| `editbox_width_frontend.edit_control_selector` | `.msg-edit` | 编辑控件外层选择器 |
