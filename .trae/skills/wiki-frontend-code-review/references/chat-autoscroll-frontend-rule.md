# Rule Catalog — Streaming Chat Auto-Scroll-to-Bottom (Frontend)

前端流式聊天「自动贴底滚动」审查规则：确保新 token / 新消息到达时正确贴底展示，且解决三类失效——①单次 `nextTick` 早于图片/代码撑高导致落后于高度；②强制拉回打断用户回看；③连续 token 单次定位落后。策略：nextTick + 双 rAF、用户上滑暂停贴底、capture 阶段监听 img load 补滚、容器挂载/卸载自动绑定解绑监听。所有参数从 `config/review-config.md` 读取，禁止硬编码。

> 复盘来源：`useChatAutoScroll.ts` 头部注释明确列出三类失效并给出解决：双 rAF 捕获同步布局变化；scroll 监听按 `NEAR_BOTTOM_PX` 阈值暂停/恢复贴底；capture 阶段 `load` 监听 img 异步撑高补滚；`watch(containerRef,{immediate})` 随容器 v-if 挂载/卸载自动 bind/unbind，避免泄漏。

## Scope
- Covers: `frontend/src/composables/**/useChatAutoScroll.ts`（scrollToBottom / onScroll / onMediaLoad / bind / unbind）、`frontend/src/views/**/Query.vue` / `frontend/src/components/**/FloatingChat.vue`（调用点 + watch messages.length）。
- Does NOT cover：纯静态、不滚动的内容区；一次性请求无流式中间态；滚动完全由用户手动控制、不需自动跟随的展示页。

## Rules

### FR-078-1: 贴底定位须 nextTick + 双 requestAnimationFrame

IsUrgent: False
Category: Chat Autoscroll

#### Description

贴底须 `nextTick` + 双 `requestAnimationFrame` 后在浏览器绘制一帧再定位 `scrollTop = scrollHeight`，确保捕获图片占位 / Markdown 渲染等同步布局变化，真正贴到最终底部（FR-078-1，建议级）。

### FR-078-2: 用户上滑超阈值暂停自动贴底、回底恢复

IsUrgent: False
Category: Chat Autoscroll

#### Description

监听容器 `scroll`，以 `near_bottom_px`（默认 80）阈值判断用户是否贴底：上滑超过阈值则 `stickToBottom = false` 暂停自动贴底，用户滑回底部恢复，避免与用户争夺滚动位置（FR-078-2，建议级）。

### FR-078-3: 捕获阶段监听 img load 异步撑高后补滚

IsUrgent: False
Category: Chat Autoscroll

#### Description

`img` 的 `load` 事件不冒泡，须在容器层以**捕获阶段**（`true`）监听 `load`，图片异步加载撑高容器后补滚一次（FR-078-3，建议级）。

### FR-078-4: 滚动/加载监听随容器生命周期绑定解绑

IsUrgent: True
Category: Chat Autoscroll

#### Description

`scroll` + `load` 监听须通过 `watch(containerRef,{immediate})` 在容器挂载时 `bind`、卸载时 `unbind`，`onBeforeUnmount` 解绑，适配 `v-if` 按需渲染面板，防止监听泄漏到已销毁节点（FR-078-4，Critical）。

### FR-078-5: force 语义——新消息始终展示，其余仅跟随

IsUrgent: False
Category: Chat Autoscroll

#### Description

`force=true` 仅用于「新消息到达」应始终贴底；非强制时仅当「流式进行且用户贴底」或「用户当前已在底部」才跟随，不强行打扰回看中的用户（FR-078-5，建议级）。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `chat_autoscroll_frontend.enabled` | `true` | 启用本组规则（FR-078） |
| `chat_autoscroll_frontend.severity_double_raf` | `major` | FR-078-1 单次 nextTick 早于布局变化的违规级别 |
| `chat_autoscroll_frontend.severity_user_pause` | `minor` | FR-078-2 未实现用户上滑暂停的违规级别 |
| `chat_autoscroll_frontend.severity_img_reflow` | `minor` | FR-078-3 未补滚图片撑高的违规级别 |
| `chat_autoscroll_frontend.severity_lifecycle` | `critical` | FR-078-4 监听未随容器生命周期绑定解绑（泄漏）的违规级别 |
| `chat_autoscroll_frontend.severity_force` | `minor` | FR-078-5 force 语义错用的违规级别 |
| `chat_autoscroll_frontend.near_bottom_px` | `80` | 判定用户贴底的阈值（px） |
| `chat_autoscroll_frontend.double_raf` | `true` | 是否要求 nextTick + 双 rAF |
| `chat_autoscroll_frontend.img_load_reflow` | `true` | 是否要求 capture 阶段监听 img load 补滚 |
