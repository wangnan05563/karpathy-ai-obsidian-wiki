# Harness 集成规范

本文档记录 Karpathy Wiki 项目中 Harness（LLM Agent 运行时）的集成标准。

## EngineAdapter 接口

Harness 通过 `EngineAdapter` 接口与业务层解耦：

```typescript
interface EngineAdapter {
  /** 工具调用执行 */
  executeTool(toolName: string, args: Record<string, unknown>): Promise<unknown>;
  /** 获取当前状态 */
  getState(): Record<string, unknown>;
  /** 决定是否重试 */
  shouldRetry(err: Error, attempt: number): boolean;
  /** 预算配置 */
  budget: { maxTokens: number; maxCost: number; currency: string };
  /** 钩子注册 */
  hooks: HookRegistry;
}
```

## 实现要求

### 1. 接口实现须完整

所有方法都必须实现，不允许省略：

```typescript
// 错误：缺少 shouldRetry
const adapter: EngineAdapter = {
  executeTool: ...,
  getState: ...,
  // shouldRetry 缺失！
  budget: ...,
  hooks: ...
};

// 正确：完整实现
const adapter: EngineAdapter = {
  executeTool: ...,
  getState: ...,
  shouldRetry: (err, attempt) => attempt < 3 && err.message.includes('timeout'),
  budget: { maxTokens: 50000, maxCost: 0.10, currency: 'USD' },
  hooks: ...
};
```

### 2. AsyncIterable 事件流须正确 yield

```typescript
// 错误：直接返回数组
function* workflow() {
  const results = await execute();
  return results; // 这不是 AsyncIterable！
}

// 正确：使用 yield
async function* workflow() {
  for await (const item of stream) {
    yield { type: 'progress', data: item };
  }
  yield { type: 'done', data: { status: 'complete' } };
}
```

### 3. 预算超限须返回部分结果

```typescript
try {
  for await (const result of harness.run(prompt)) {
    yield result;
  }
} catch (err) {
  if (err.message.includes('budget exceeded')) {
    // 返回部分结果，而非中断
    yield { type: 'done', data: { status: 'partial', reason: 'budget_exceeded' } };
  } else {
    throw err;
  }
}
```

## Hook 注册

Hook 用于在关键节点执行确定性逻辑：

```typescript
interface HookRegistry {
  /** 工具调用前 */
  onToolCall?: (name: string, args: unknown) => void;
  /** 预算警告 */
  onBudgetWarning?: (usage: number, limit: number) => void;
  /** 完成 */
  onComplete?: (result: unknown) => void;
  /** 错误 */
  onError?: (err: Error) => void;
}
```

## Prompt 单点存储

Prompt 模板必须集中管理，禁止散落在代码中：

```typescript
// 正确：集中管理
const PROMPT_TEMPLATES = {
  compile: '编译 wiki 页面。主题：{topic}',
  query: '查询 wiki 知识。问题：{question}'
};

function getPrompt(type: string, params: Record<string, string>): string {
  const template = PROMPT_TEMPLATES[type];
  if (!template) throw new Error(`Unknown prompt type: ${type}`);
  return Object.entries(params).reduce(
    (p, [k, v]) => p.replace(`{${k}}`, v),
    template
  );
}

// 错误：散落在各处
const prompt1 = '编译 wiki 页面。主题：' + topic;
const prompt2 = '查询 wiki 知识。问题：' + question;
```
