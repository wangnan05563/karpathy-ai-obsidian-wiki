# 架构模式知识库

本文档记录 Karpathy Wiki 项目的核心架构模式与设计决策，供开发时参考。

## 阶段1 架构（TRAE CLI 桥接 API）

早期开发阶段通过 TRAE CLI 直接调用后端 API，形成以下模式：

- **CLI 桥接模式**：TRAE CLI 作为 LLM 代理，通过 HTTP 调用 Fastify 路由
- **SSE 流式响应**：所有耗时操作（编译/查询）均通过 SSE 流式返回结果
- **幂等操作**：所有 API 端点设计为幂等，支持重试

## 阶段2 架构（自研 Harness + 业务层）

当前阶段引入了 harness 层，形成三层架构：

```
Frontend (Vue 3) → API Routes (Fastify) → Harness (LLM Agent) → Vault (File System)
```

### EngineAdapter 接口模式

Harness 通过 `EngineAdapter` 接口与业务层解耦：

```typescript
interface EngineAdapter {
  executeTool(toolName: string, args: Record<string, unknown>): Promise<unknown>;
  getState(): Record<string, unknown>;
  shouldRetry(err: Error, attempt: number): boolean;
  budget: { maxTokens: number; maxCost: number };
  hooks: HookRegistry;
}
```

**设计意图**：使同一 harness 可以适配不同的 LLM provider 和工具集。

### 事件桥接模式（bridgeHarnessToEvents）

Harness 内部事件 → SSE 事件的转换通过桥接函数完成：

```typescript
async function* bridgeHarnessToEvents(harness: Harness): AsyncIterable<SSEEvent> {
  for await (const internalEvent of harness.stream()) {
    yield mapToSSEEvent(internalEvent);
  }
}
```

**关键点**：
- 使用 generator 函数实现懒求值
- 事件类型映射集中在 `mapToSSEEvent` 中维护
- 错误事件通过 `error` 类型统一推送

### 注册式资源模式

后端路由采用注册式管理：

1. 每个路由模块在 `routes/` 下独立文件
2. `routes/index.ts` 统一注册所有路由
3. 新增路由必须同步更新 index.ts，否则 404

**判断信号**：新增路由文件后未注册 → 访问返回 404 或 500。

### 配置热加载模式

项目使用 `config.json` 管理配置，分为两类：

| 类型 | 说明 | 示例 |
|---|---|---|
| 热加载 | 修改后立即生效 | SSE 超时时间、日志级别 |
| 需重启 | 修改后需重启服务 | 端口号、数据库路径、LLM API Key |

**判断规则**：涉及网络监听、文件句柄、进程级状态配置必须重启。

### 幂等操作模式

init 时检查文件是否存在的模式：

```typescript
async function initVault(vaultId: string): Promise<void> {
  const exists = await vaultService.exists(vaultId, 'config.json');
  if (exists) return; // 已存在则跳过
  await vaultService.writeFile(vaultId, 'config.json', DEFAULT_CONFIG);
}
```

**适用场景**：所有初始化操作、种子数据写入、默认配置创建。

## 适用场景

- 新功能开发时参考对应架构模式
- 代码评审时检查是否符合既定模式
- 重构时保持架构一致性

## 不适用场景

- 不涉及 harness 的简单 CRUD 操作
- 纯前端 UI 组件开发
