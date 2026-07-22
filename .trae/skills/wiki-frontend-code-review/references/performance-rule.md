# Rule Catalog — Performance

性能审查规则：确保大图分级降级、SSE 连接管理、资源懒加载等性能关键点合规。所有参数从 `config/review-config.md` 读取，禁止在规则文件中硬编码。

## vis-network 大图分级降级

IsUrgent: True
Category: Performance

### Description

vis-network 在节点数较大时渲染与物理仿真开销急剧上升，须按节点数分级降级（具体阈值见 `config/review-config.md`，默认 L1/L2/L3 三级）。达到降级阈值时：关闭平滑曲线、简化节点样式、减少稳定化迭代次数。在 `setData` 前根据节点数选择配置，避免运行时卡顿。

### Suggested Fix

封装 `buildNetworkOptions(nodeCount)`，按阈值返回不同 options；切换数据时调用。

> **示例代码**: 参见 [examples/performance-rule-examples.md](examples/performance-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## vis-network 实例须在 onBeforeUnmount 中 destroy

IsUrgent: True
Category: Performance

### Description

`vis.Network` 实例持有 Canvas、事件监听、动画帧等资源，组件卸载时不调用 `destroy()` 会造成内存泄漏与幽灵事件触发。必须成对：`onMounted` 创建，`onBeforeUnmount` 销毁。

### Suggested Fix

把 Network 实例存到 ref，在 `onBeforeUnmount` 中调用 `network.value?.destroy()`。

> **示例代码**: 参见 [examples/performance-rule-examples.md](examples/performance-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## 窄屏切换列表视图，减少 Canvas 渲染

IsUrgent: False
Category: Performance

### Description

窄屏（宽度 < 断点，默认 768px，见 `config/review-config.md`）下 vis-network 的 Canvas 渲染开销相对收益过低，须自动切换为列表视图。通过监听 `resize` 事件（防抖）判断当前宽度，切换视图状态变量。

### Suggested Fix

封装 `useBreakpoint()` 或在组件内监听 resize 切换 `viewMode`，卸载时移除监听。

> **示例代码**: 参见 [examples/performance-rule-examples.md](examples/performance-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## SSE 消费用 ReadableStream 逐块解析，禁止 await 全量

IsUrgent: True
Category: Performance

### Description

SSE 流式响应必须用 `ReadableStream` + `TextDecoder` 逐块读取并按行解析，边接收边更新 UI。禁止 `await response.text()` / `await response.json()` 把整段响应读完再处理——这会丢失流式体验、首字延迟变高、大响应可能撑爆内存。

### Suggested Fix

改用 `response.body.getReader()` 循环读取，维护一个 buffer 处理跨块的换行。

> **示例代码**: 参见 [examples/performance-rule-examples.md](examples/performance-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## 事件监听须在 onBeforeUnmount 移除

IsUrgent: True
Category: Performance

### Description

`window`/`document` 上的 `resize`/`scroll`/`keydown` 等监听必须在 `onBeforeUnmount` 中移除，且移除的函数引用须与注册时一致（避免使用内联箭头函数导致引用不同）。遗漏移除会造成组件卸载后仍触发回调、访问已销毁的 ref。

### Suggested Fix

把监听函数提取为具名引用，注册与移除使用同一引用；必要时包一层防抖。

> **示例代码**: 参见 [examples/performance-rule-examples.md](examples/performance-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## 列表渲染用 :key 绑定唯一 ID，禁止 index 作 key

IsUrgent: True
Category: Performance

### Description

`v-for` 必须用数据自身的稳定唯一 ID 作为 `:key`，禁止用数组索引 `index`。用 index 作 key 时，列表增删或排序会导致 Vue 复用错误的 DOM、内部状态错位、组件生命周期异常触发。

### Suggested Fix

确认数据项有 `id` 字段（或其它稳定唯一键），绑定到 `:key`；缺失 ID 时在后端补齐或前端生成稳定 key。

> **示例代码**: 参见 [examples/performance-rule-examples.md](examples/performance-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## SSE 连接管理必须清理，done 事件必须正确结束流

IsUrgent: True
Category: Performance

### Description

SSE（Server-Sent Events）连接管理须满足以下要求：

1. **统一封装**：使用 `consumeSSEStream` 统一消费函数，禁止手动构造 `EventSource` 未清理。
2. **连接清理**：SSE 连接必须在 `onBeforeUnmount` 中关闭，否则连接泄漏导致内存泄漏。
3. **done 事件处理**：`done` 事件必须正确结束流并关闭连接，未处理 `done` 事件会导致连接泄漏。
4. **错误降级**：SSE 连接失败必须有降级提示（ElMessage），网络中断有重连逻辑（参见 [async-reliability-rule.md](async-reliability-rule.md) AR-2）。

### Suggested Fix

```typescript
// ❌ 手动构造 EventSource 未清理
const es = new EventSource('/api/stream');
es.onmessage = (event) => { /* 处理消息 */ };
// 未在 onBeforeUnmount 中 es.close()

// ✅ 统一封装 + 生命周期清理
const { close } = consumeSSEStream('/api/stream', {
  onMessage(event) { /* 处理消息 */ },
  onDone() { /* 流结束 */ },
  onError(err) { ElMessage.error('流式响应中断'); },
});
onBeforeUnmount(() => { close(); });
```

> **示例代码**: 参见 [examples/performance-rule-examples.md](examples/performance-rule-examples.md)。
