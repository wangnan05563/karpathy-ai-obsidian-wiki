# 流式聊天自动贴底滚动（双 rAF + 用户暂停 + 图片补滚）

**代码**：CODING-STREAMING-AUTOSCROLL
**严重级别**：major

## 问题（Problem）

流式输出（SSE / token 流）聊天界面需要「新内容到达时自动滚到底部」以展示最新 token。朴素实现有三处失效：

① **单次 `nextTick` 定位过早**：异步内容（图片懒加载、Markdown 代码块渲染）在 `nextTick` 时尚未撑高容器，定位到的 `scrollTop` 落后最终高度，用户看不到最新 token；
② **用户上滑阅读被强制拉回底部**：流式进行中持续 `scrollTop = scrollHeight` 会打断用户回看，体验割裂；
③ **连续 token 涌入时单次定位落后节奏**：分片高频到达，单次定位赶不上高度增长。

> 真实代码佐证（`frontend/src/composables/useChatAutoScroll.ts`）：文件头部注释明确列出上述三类失效，并以 `nextTick + 双 requestAnimationFrame`、容器 `scroll` 监听判断贴底、`capture` 阶段拦截 `img` `load` 补滚、容器挂载/卸载自动绑定/解绑监听解决。

## 规则（Rule）

### R-1：定位须 `nextTick` + 双 `requestAnimationFrame`，捕获同步布局变化

滚动到底部须在 Vue 完成 DOM 更新（`nextTick`）**且**浏览器绘制一帧（双 `requestAnimationFrame`）之后执行，确保捕获图片占位 / Markdown 渲染等同步布局变化，真正贴到最终底部。

```typescript
function scrollToBottom(force = false) {
  const el = containerRef.value;
  if (!el) return;
  if (force || (isStreaming() && stickToBottom) || nearBottom(el)) {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => { el.scrollTop = el.scrollHeight; });
    });
  }
}
```

### R-2：用户上滑超过阈值即暂停自动贴底，回到底部自动恢复

监听容器 `scroll`，以 `NEAR_BOTTOM_PX`（默认 80px）阈值判断用户是否贴近底部：上滑超过阈值则 `stickToBottom = false` 暂停自动贴底；用户滑回底部则恢复。避免与用户争夺滚动位置。

### R-3：捕获阶段监听 `img` `load`，图片异步撑高后补滚一次

`img` 的 `load` 事件不冒泡，须在容器层以**捕获阶段**（`true`）监听 `load`，图片异步加载撑高容器后补滚一次，保证带图消息也能贴底。

### R-4：容器挂载 / 卸载自动绑定 / 解绑监听，避免泄漏

通过 `watch(containerRef, {immediate})` 在容器出现 / 消失时自动 `bind` / `unbind` `scroll` + `load` 监听；`onBeforeUnmount` 解绑。适配 FloatingChat 这类 `v-if` 按需渲染面板，防止监听器泄漏到已销毁节点。

### R-5：`force` 语义清晰——新消息始终展示，其余仅跟随

`force=true` 用于「新消息到达」应始终贴底展示；非强制时仅当「流式进行且用户贴底」或「用户当前已在底部」才跟随，不强行打扰回看中的用户。

## 适用 / 不适用

- **适用**：任何 SSE / 流式 token 输出的聊天 / 问答 / 长文生成界面；含图片 / 代码块等异步撑高内容的消息流；用户可能在生成过程中回看历史的场景。
- **不适用**：纯静态、不滚动的内容区；一次性请求无流式中间态；滚动位置由用户完全手动控制、不需要自动跟随的展示页。

## 检查清单

- [ ] 贴底定位是否 `nextTick` + 双 `requestAnimationFrame`（`chat_autoscroll.double_raf`）
- [ ] 是否按 `NEAR_BOTTOM_PX` 阈值暂停 / 恢复自动贴底（`chat_autoscroll.near_bottom_px`）
- [ ] 是否 `capture` 阶段监听 `img` `load` 补滚（`chat_autoscroll.img_load_reflow`）
- [ ] 容器 `scroll` / `load` 监听是否在挂载绑定、卸载解绑，无泄漏（`chat_autoscroll.bind_unbind`）
- [ ] `force` 仅用于新消息到达，其余仅跟随用户贴底状态（`chat_autoscroll.force_semantics`）
