# 阅读视野优化与输入区固定规则（CODING-032）

> 复盘来源：知识库问答窗口标题头占比过大导致阅读视野狭窄；改造时输入框未固定底部，滚动时输入框随内容上移不可见。
> 所有可变参数从 `config/coding-standards-config.md` 的 `reading_viewport` 字段读取，禁止在规则文件中硬编码像素值或 CSS 属性。

## 规则

**长内容阅读型视图（问答、文档、聊天）必须满足**：
1. 标题头区域高度 ≤ `reading_viewport.max_header_ratio`（默认 15%）的可视高度
2. 输入区固定在底部，使用 `position: sticky; bottom: 0` + 毛玻璃背景保证内容可读
3. 内容区域可用高度 ≥ `reading_viewport.min_content_ratio`（默认 75%）的可视高度

## 适用场景

- 问答 / 聊天 / 对话窗口（Query.vue 类）
- 文档阅读视图（Reader.vue / Document.vue 类）
- 长列表浏览视图（Browse.vue 在内容较多时）
- 任何需要边滚动阅读边输入的视图

## 不适用场景

- 配置表单页（Form.vue 类，标题与输入框同等重要）
- 仪表盘（Dashboard.vue 类，无长内容阅读需求）
- 图谱可视化（Graph.vue 类，Canvas 占据全部视野）
- 健康检查页（Health.vue 类，无输入区）
- 移动端 App（移动端有独立的输入区设计规范）

## 设计流程

```
设计阅读型视图
   ↓
1. 计算可视高度（100vh - 导航栏 - 其他固定元素）
   ↓
2. 标题头区域 ≤ max_header_ratio × 可视高度
   ↓
   超过 → 去除非必要元素（图标、描述、副标题）
   ↓
3. 内容区域 ≥ min_content_ratio × 可视高度
   ↓
   不足 → 调整 calc() 公式，减少固定元素占用
   ↓
4. 输入区固定在底部：
   - position: sticky; bottom: 0
   - 毛玻璃背景：background: rgba(R, G, B, 0.85); backdrop-filter: blur(12px)
   - z-index 高于内容区
   ↓
5. 验证：滚动到底部时输入区仍可见
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `reading_viewport.enabled` | `true` | 是否启用阅读视野守卫 |
| `reading_viewport.severity` | `error` | 违规严重级别 |
| `reading_viewport.applicable_views` | `Query, Reader, Document, Chat, Browse` | 适用视图列表（逗号分隔） |
| `reading_viewport.max_header_ratio` | `0.15` | 标题头区域最大占比（15%） |
| `reading_viewport.min_content_ratio` | `0.75` | 内容区最小占比（75%） |
| `reading_viewport.input_bar_position` | `sticky bottom` | 输入区定位策略 |
| `reading_viewport.input_bar_z_index` | `2` | 输入区 z-index（高于内容区） |
| `reading_viewport.input_bar_background` | `rgba(var(--bg-scene-rgb), 0.85)` | 毛玻璃背景（CSS 变量形式，跟随主题） |
| `reading_viewport.input_bar_backdrop_filter` | `blur(12px)` | 毛玻璃模糊滤镜 |
| `reading_viewport.input_bar_padding` | `12px 4px 4px` | 输入区内边距 |
| `reading_viewport.calc_template` | `calc(100vh - {nav_height}px - {other_fixed}px)` | 内容区高度计算模板 |

## 检查方式

1. **适用视图识别**：视图文件名匹配 `applicable_views` 列表时启用检查
2. **标题头比例检查**：通过浏览器 DevTools 测量标题头高度 / 可视高度，超过 `max_header_ratio` 即违规
3. **输入区定位检查**：CSS 中 `.input-bar` 或类名包含 `input` 的选择器必须有 `position: sticky; bottom: 0`
4. **毛玻璃背景检查**：输入区背景必须是半透明 + `backdrop-filter: blur()`，禁止纯不透明背景
5. **z-index 检查**：输入区 z-index 必须 ≥ `input_bar_z_index`

## 正确示例

```vue
<template>
  <!-- 极简标题头（仅 ModelSelector + 新会话按钮） -->
  <div class="query-topbar">
    <ModelSelector />
    <el-button v-if="messages.length > 0" size="small" @click="handleNewSession">
      新会话
    </el-button>
  </div>
  
  <!-- 内容区（扩大阅读视野） -->
  <div class="messages-area">
    <MessageItem v-for="m in messages" :key="m.id" :message="m" />
  </div>
  
  <!-- 输入区固定底部 + 毛玻璃 -->
  <div class="input-bar">
    <InputToolbar v-model="mode" />
    <AttachmentUploader />
    <textarea v-model="input" />
    <button @click="send">发送</button>
  </div>
</template>

<style scoped>
.query-topbar {
  /* 标题头占比 ≤ 15% */
  height: 40px;
  padding: 8px 20px;
  display: flex;
  justify-content: space-between;
}

.messages-area {
  /* 内容区 ≥ 75% */
  height: calc(100vh - 160px);  /* 100vh - 导航栏(60px) - 标题头(40px) - 输入区(60px) */
  overflow-y: auto;
  padding: 16px 20px;
}

.input-bar {
  /* 输入区固定底部 */
  position: sticky;
  bottom: 0;
  padding: 12px 4px 4px;
  background: rgba(var(--bg-scene-rgb), 0.85);
  backdrop-filter: blur(12px);
  border-radius: 0 0 var(--radius-card, 16px) var(--radius-card, 16px);
  z-index: 2;
}
</style>
```

## 错误示例

```vue
<!-- 错误：标题头占比过大 -->
<div class="query-head">
  <RobotAvatar :size="64" />  <!-- 64px 大图标 -->
  <h1>知识库问答</h1>          <!-- 大标题 -->
  <p>基于 Obsidian 的智能问答系统</p>  <!-- 长描述 -->
  <ModelSelector />
  <button>新会话</button>
  <button>导出</button>
  <button>历史记录</button>
</div>
<!-- 标题头高度约 120px，占比 16.7%，超过 max_header_ratio -->

<!-- 错误：输入区未固定底部 -->
<div class="input-bar">
  <textarea v-model="input" />
  <button @click="send">发送</button>
</div>
<style>
.input-bar {
  /* 缺少 position: sticky; bottom: 0 */
  margin-top: 8px;
}
</style>
<!-- 滚动到底部时输入框不可见 -->

<!-- 错误：输入区背景不透明 -->
.input-bar {
  position: sticky;
  bottom: 0;
  background: var(--bg-card);  /* 纯不透明，遮挡内容 */
  /* 缺少 backdrop-filter: blur() */
}
```

## 适配新项目

- 适配移动端项目：`input_bar_position` 改为 `fixed bottom`（移动端 sticky 兼容性问题），`max_header_ratio` 改为 `0.1`
- 适配桌面端固定窗口：`min_content_ratio` 改为 `0.8`（窗口已固定大小，可利用空间更多）
- 适配无输入区视图：从 `applicable_views` 中移除该视图名
- 适配多输入区视图（如评论 + 主输入）：`input_bar_position` 保持 `sticky bottom`，主输入区在最底部

## 与其他规则的关系

- 与滚动容器规则（CODING-016 硬约束）联动：本规则关注"阅读视野占比"，CODING-016 关注"滚动容器单一职责"
- 与主题感知图标规则（CODING-023 硬约束）独立：本规则关注布局，CODING-023 关注图标设计
- 与导航栏双模式规则（CODING-024 硬约束）配合：导航栏折叠后释放更多阅读视野
