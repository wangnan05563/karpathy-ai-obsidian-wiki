# Parallel Loading Rule

## 触发关键词
Promise.allSettled, for await, 串行加载, 并行加载, MCP, 多资源, tools/list

## 规则

### PL-1：N 个独立资源加载必须用 Promise.allSettled
**严重级别**：critical

N 个无依赖关系的资源加载（如 MCP 服务器连接、多 API 调用、多文件读取）必须用 `Promise.allSettled` 并行加载，禁止用 `for await...of` 串行加载。

**为什么**：串行加载总耗时 = N × 单次超时（如 2×30s=60s），并行加载总耗时 = max(单次耗时)，性能差异随 N 线性放大。历史问题：MCP 工具串行加载 2×30s=60s 刚好触发前端 60s 超时，AI 回复被丢弃。

**实现模式**：
```typescript
// 反模式：串行加载，单失败阻断全部
const results = [];
for (const server of servers) {
  const tools = await listTools(server, timeout); // 串行，单失败抛异常中断
  results.push(...tools);
}

// 正确模式：并行加载，单失败收集到 errors 不阻断
const settled = await Promise.allSettled(
  servers.map(async (server) => {
    const tools = await listTools(server, timeout);
    return tools;
  }),
);
// 收集结果：fulfilled 合并，rejected 转 errors
for (let i = 0; i < settled.length; i++) {
  const r = settled[i];
  if (r.status === 'fulfilled') {
    results.push(...r.value);
  } else {
    errors.push({
      source: servers[i].name,
      message: r.reason instanceof Error ? r.reason.message : String(r.reason),
    });
  }
}
```

### PL-2：为什么用 allSettled 而非 all
**严重级别**：critical

必须用 `Promise.allSettled` 而非 `Promise.all`。`Promise.all` 任一 reject 会让整个 await reject，导致其他成功的结果被丢弃；`allSettled` 总是 resolve，失败结果在数组中以 rejected 状态呈现，调用方可分别处理成功与失败。

**为什么**：单资源失败不应阻断其他资源加载。MCP 服务器 A 超时不应导致服务器 B 的工具被丢弃。

### PL-3：失败结果必须收集到 errors 数组并降级处理
**严重级别**：critical

单个资源加载失败时，必须将错误信息收集到 `errors` 数组返回给调用方，主流程继续处理成功的资源，禁止抛异常中断整体。

**实现模式**：
```typescript
// 失败信息结构必须包含 source 字段标识来源
errors.push({
  source: `mcp:${server.name}`,
  message: reason instanceof Error ? reason.message : String(reason),
});
// 调用方按 errors 数组决定降级策略（如跳过 MCP 工具，仅用内置工具）
```

### PL-4：同一资源内的多个子任务可同步处理
**严重级别**：best-practice

同一资源（如同一 MCP 服务器）内的多个子任务（如多个工具构建）可同步 for 循环处理，无需再并行。并行层级应聚焦在"资源"粒度，而非"子任务"粒度。

**为什么**：子任务通常是内存操作（如构建工具定义对象），耗时可忽略；过度并行反而增加调度开销与代码复杂度。

### PL-5：并行加载必须有总超时兜底
**严重级别**：suggestion

并行加载整体应有总超时兜底（`Promise.race` + timeout），防止单个资源卡死导致整体永不返回。虽然 `allSettled` 会等待所有 settle，但单个资源可能因底层连接永不超时而永久挂起。

**实现模式**：
```typescript
const results = await Promise.race([
  Promise.allSettled(tasks),
  new Promise((_, reject) => setTimeout(() => reject(new Error('parallel timeout')), totalTimeout)),
]);
```

## 适用场景
- N 个独立资源加载（MCP 服务器、多 API、多文件）
- 资源间无依赖关系
- 单资源失败不应阻断整体

## 不适用场景
- 资源间有依赖关系（B 需要 A 的结果）→ 必须串行
- 单资源加载（N=1）→ 直接 await 即可
- 资源加载有严格顺序要求（如认证 → 数据 → 渲染）

## 检查清单
- [ ] N 个独立资源加载是否用 `Promise.allSettled`
- [ ] 是否用 `allSettled` 而非 `all`
- [ ] 失败结果是否收集到 errors 数组并降级
- [ ] 并行层级是否聚焦在资源粒度而非子任务
- [ ] 是否有总超时兜底防止永久挂起
