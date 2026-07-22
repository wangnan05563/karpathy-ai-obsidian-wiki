# 错误处理规范

本文档记录 Karpathy Wiki 项目的错误处理标准模式。

## 核心原则

### 1. try-catch 必须用 err instanceof Error 守卫

```typescript
try {
  await someAsyncOp();
} catch (err) {
  // 正确：类型守卫
  const msg = err instanceof Error ? err.message : 'Unknown error';
  throw new Error(msg);
  
  // 错误：直接访问 .message 可能导致运行时错误
  const msg = (err as Error).message;
}
```

### 2. SSE 流中错误须通过 error 事件推送

```typescript
app.get('/api/wiki/compile', async (request, reply) => {
  try {
    for await (const event of stream) {
      reply.raw.write(formatSSE(event));
    }
  } catch (err) {
    // 错误必须通过 error 事件推送，不能直接 throw
    const msg = err instanceof Error ? err.message : 'Unknown error';
    reply.raw.write(`event: error\ndata: {"message":"${msg}"}\n\n`);
  } finally {
    reply.raw.end();
  }
});
```

### 3. 外部错误须转为用户友好消息

```typescript
try {
  await callExternalAPI(url);
} catch (err) {
  // 不暴露内部 URL 或技术细节
  throw new Error('外部服务暂时不可用，请稍后重试');
}
```

### 4. 工具执行失败须 catch 并返回错误描述给 LLM

```typescript
async function executeTool(name: string, args: unknown) {
  try {
    return await toolRegistry.execute(name, args);
  } catch (err) {
    // 返回结构化错误，供 LLM 理解并重试
    return {
      success: false,
      error: err instanceof Error ? err.message : '工具执行失败',
      tool: name
    };
  }
}
```

### 5. 状态文件损坏须优雅降级

```typescript
async function loadState(filePath: string): Promise<State> {
  try {
    const content = await readFile(filePath, 'utf-8');
    return JSON.parse(content) as State;
  } catch (err) {
    // 文件不存在：返回默认状态
    if ((err as NodeJS.ErrnoException).code === 'ENOENT') {
      return DEFAULT_STATE;
    }
    // 解析失败：记录警告，返回默认状态
    console.warn(`状态文件损坏，使用默认状态: ${filePath}`);
    return DEFAULT_STATE;
  }
}
```

## 错误码约定

| 错误码 | 含义 | 处理方式 |
|---|---|---|
| `VAULT_NOT_FOUND` | Vault 不存在 | 创建新 Vault |
| `WRITE_DENIED` | 写入路径不在白名单 | 拒绝并提示 |
| `TIMEOUT` | 操作超时 | 重试一次 |
| `RATE_LIMITED` | 触发限流 | 退避重试 |
| `PARSE_ERROR` | 数据解析失败 | 降级到默认值 |
| `UNKNOWN` | 未知错误 | 记录日志并返回通用消息 |

## 日志级别约定

| 级别 | 使用场景 | 示例 |
|---|---|---|
| ERROR | 不可恢复的错误 | 数据库连接失败 |
| WARN | 可恢复的问题 | 外部服务超时（已重试） |
| INFO | 正常业务流程 | 编译开始/结束 |
| DEBUG | 调试信息 | 中间变量值 |
