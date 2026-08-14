# CODING-PERSISTENT-COMPONENT — 常驻组件生命周期隔离与按需渲染

> 对应前端 FR-086 / 后端 BR-096（部署验证侧）/ wiki-auto-testing `frontend_review_static_check` 派生组。
> 基于「移动端聆听页用 v-show 常驻 `<audio>` 实现切 Tab 后台播放」四维度复盘。

## 问题背景

单 SPA 无 vue-router，移动端 `MobileShell` 复用 stores、`v-if` 互斥挂载各 Tab。要实现"切 Tab 保持播放、切回自动定位"，
须把聆听页从 `v-else-if` 链改为 `v-show` 常驻——使 `<audio>` 与本地播放状态（queue / currentIndex / isPlaying / position）不随 Tab 切换卸载。

`v-show` 常驻带来三类新陷阱（见「适用/不适用」）：

1. **`onMounted` 只执行一次**：组件常驻后，Tab 切换不再触发挂载，原依赖 `onMounted` 做的"账户切换重置 / 数据重载"全部失效。
2. **重型 DOM 常驻成本**：知识库含 1000+ page 节点，常驻使整棵重列表始终留在 DOM，增加内存与重排成本。
3. **会话作用域状态残留**：上一账户的音色 / 队列在账户切换后仍残留（与 `MobileShell` 账户重置约定冲突）。

## 规则（4 条）

### PC-1 切回恢复与自动定位（watch visible）
`v-show` 常驻组件须用 `watch(() => props.visible)` 在切回时恢复状态 / 自动定位，而非依赖 `onMounted`（只跑一次）。
- 切回聆听 Tab → 平滑滚动到当前播放项（`scrollIntoView({behavior:'smooth',block:'center'})`）。
- 切出时可选暂停 UI 态但保留 `<audio>` 播放（后台播放需求）。

### PC-2 账户切换显式重置（watch auth）
凡因 `v-show` 常驻导致 `onMounted` 仅一次执行的组件，账户切换 / 登出时**必须**显式重置会话作用域状态：
暂停音频 → `revokeObjectURL` → 清空 `queue / currentIndex / isPlaying / position / duration` → 重载本账户默认配置（音色 / 语速）。
```ts
watch(
  () => authStore.user?.id,
  async (newId, oldId) => {
    if (newId === oldId) return;
    audioEl.value?.pause();
    if (objectUrl) { URL.revokeObjectURL(objectUrl); objectUrl = null; }
    isPlaying.value = false; currentIndex.value = -1; queue.value = [];
    position.value = 0; duration.value = 0;
    const cfg = await loadTtsConfig(newId ?? 'guest');
    voice = cfg.voice || 'zh-CN-XiaoxiaoNeural';
  },
);
```

### PC-3 重型 DOM 按可见性懒渲染（v-if visible 包裹）
常驻组件内部"非播放必需"的重型节点（长列表 / 搜索结果 / 目录树）用 `v-if="visible"` 包裹，仅 Tab 激活时渲染；
"播放必需"的状态（`<audio>` / queue / position / 播放器 UI）保留在 `v-show` 容器内，保证后台播放不受影响。
- 适用：列表 > 数百节点、含图片 / 富文本的重内容区。
- 不适用：轻量列表（< 50 项）、纯文本短列表——`v-if` 包裹反而增加切换闪烁，直接常驻即可。

### PC-4 vue-tsc 模板类型收窄（v-show 改造附带）
把某分支移出 `v-else-if` 链后，原 `MobilePlaceholder` 的 `v-else-if="activeTab!=='me'"` 会错误匹配被移出的分支。
修复：将 placeholder 改为**独立 `v-if` 排除全部已知 Tab**（query/browse/ingest/me/listen），让 TS 把 `activeTab` 收窄为 `never` 通过索引类型。
```vue
<MobilePlaceholder v-if="!['query','browse','ingest','me','listen'].includes(activeTab)" />
```
- 不适用：使用 vue-router 的项目（`router-view` 天然处理视图切换，无 `v-else-if` 链收窄问题）。

## 适用 / 不适用（维度④）

| 适用场景 | 不适用场景 |
|---------|-----------|
| 用 `v-show` 常驻以保留**后台状态**（音频播放 / 长连接 / 计时器 / 流式进度）的组件 | 纯展示、无后台状态、生命周期短的组件（用 `v-if` 即可，无需常驻） |
| 单 SPA 无 vue-router、用 `v-show`/`v-if` 手动切换视图 | 用 vue-router 的项目（路由守卫 + `<router-view>` 已处理生命周期，PC-4 模板收窄不适用） |
| 账户 / 租户切换会影响组件内会话态（须 watch auth 重置） | 无账户概念、全局单用户的前端 |
| 组件内含数百+ 重型节点（须 `v-if="visible"` 懒渲染降内存） | 轻量列表（< 50 项），`v-if` 包裹只增切换闪烁 |

## 对应审查要点

- 前端：`wiki-frontend-code-review` FR-086（persistent-component-lifecycle-frontend-rule.md）。
- 测试：`wiki-auto-testing` `frontend_review_static_check` 派生组 `persistent_component_visible_watch`（扫描 `v-show` 常驻组件是否含 `watch(visible)` 与 `watch(user?.id)` 重置，缺失即告警）。
