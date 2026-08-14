# FR-086 — 常驻组件生命周期隔离与按需渲染

> 对应 wiki-code-dev CODING-PERSISTENT-COMPONENT（PC-1~PC-4）；wiki-auto-testing `frontend_review_static_check` 派生组 `persistent_component_visible_watch`。
> 基于「移动端聆听页用 v-show 常驻 `<audio>` 实现切 Tab 后台播放」四维度复盘（含 Sequential Thinking）。

## 规则要点

当组件用 `v-show`（而非 `v-if`）常驻以保留后台状态（音频播放 / 长连接 / 计时器 / 流式进度）时，须满足：

- **FR-086-1（watch visible 切回恢复，Major）**：`v-show` 常驻组件必须用 `watch(() => props.visible)` 在切回时恢复状态 / 自动定位（如平滑滚动到当前播放项），不能依赖 `onMounted`（常驻后只跑一次）。
- **FR-086-2（watch auth 重置会话态，Critical）**：凡因常驻导致 `onMounted` 仅一次执行的组件，账户切换 / 登出时**必须**显式重置会话作用域状态——暂停音频、`revokeObjectURL`、清空 `queue/currentIndex/isPlaying/position/duration`、重载本账户默认配置。缺失会导致上一账户音色 / 队列残留（与 `MobileShell` 账户重置约定冲突）。
- **FR-086-3（重型 DOM 懒渲染，Major）**：常驻组件内部"非播放必需"的重型节点（> `heavy_list_threshold` 项的列表 / 搜索结果 / 目录树）须用 `v-if="visible"` 包裹，仅 Tab 激活时渲染；`<audio>`/queue/position/播放器 UI 保留在 `v-show` 容器保证后台播放。
- **FR-086-4（vue-tsc 模板收窄，Suggestion）**：把分支移出 `v-else-if` 链后，`MobilePlaceholder` 改为独立 `v-if` 排除全部已知 Tab（如 `!['query','browse','ingest','me','listen'].includes(activeTab)`），让 TS 把 `activeTab` 收窄为 `never` 通过索引类型。

## Wrong / Right

```vue
<!-- Wrong：v-show 常驻但无 watch(visible)/watch(auth)，切回不恢复、账户切换残留 -->
<MobileListen v-show="activeTab === 'listen'" />

<!-- Right -->
<MobileListen v-show="activeTab === 'listen'" :visible="activeTab === 'listen'" />
```
```ts
// Right：账户切换显式重置
watch(() => authStore.user?.id, async (newId, oldId) => {
  if (newId === oldId) return;
  audioEl.value?.pause();
  if (objectUrl) { URL.revokeObjectURL(objectUrl); objectUrl = null; }
  isPlaying.value = false; currentIndex.value = -1; queue.value = [];
  position.value = 0; duration.value = 0;
  const cfg = await loadTtsConfig(newId ?? 'guest');
  voice = cfg.voice || 'zh-CN-XiaoxiaoNeural';
});
```

## 适用 / 不适用（维度④）

- **适用**：用 `v-show` 常驻保留后台状态的组件；单 SPA 无 vue-router 手动切换视图；账户切换影响组件内会话态；含数百+ 重型节点的组件。
- **不适用**：纯展示 / 生命周期短的组件（用 `v-if` 即可）；使用 vue-router 的项目（路由守卫已处理，FR-086-4 模板收窄不适用）；轻量列表（< `heavy_list_threshold` 项，`v-if` 包裹只增闪烁）。

## 参数（来自 config/review-config.md `persistent_component_frontend` 段，零硬编码）

`watch_visible_signal` / `auth_watch_signal` / `heavy_dom_lazy_visible` / `heavy_list_threshold` / `template_narrow_exclude_tabs` / `severity`。
