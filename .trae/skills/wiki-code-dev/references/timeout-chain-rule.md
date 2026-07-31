# Timeout Chain Rule

## 触发关键词
timeout, 超时, AbortController, QUESTION_TIMEOUT, 阈值, mcpTimeoutMs, 链式

## 规则

### TC-1：超时阈值必须自下而上递增覆盖
**严重级别**：critical

多层调用链（前端 → 后端 → 第三方 → LLM）的超时阈值必须自下而上递增，每层超时必须覆盖下层所有耗时之和 + 安全余量。

**为什么**：上层超时 < 下层耗时会导致下层实际有结果但上层已中断，结果被丢弃。历史问题：前端 60s 超时恰好等于 MCP 加载 60s（2×30s 串行），AI 实际有回复但前端已 abort。

**阈值计算公式**（所有阈值从 `config/coding-standards-config.md` 的 `timeout_chain` 段读取，禁止在源码硬编码）：
```
前端超时 = 后端超时 + 安全余量
后端超时 = max(MCP 加载耗时, LLM 首字节延迟, 工具执行耗时) + 安全余量
MCP 加载耗时 = max(单服务器加载耗时) × 并行度修正系数
```

**实现模式**（数值为示例，实际从 config 读取）：
```typescript
// 所有阈值从 config.timeout_chain.layer_timeouts 读取，禁止硬编码
import { config } from './config';
const QUESTION_TIMEOUT_MS = config.timeout_chain.layer_timeouts.questionTimeoutMs; // 默认 120000
const mcpTimeoutMs = config.timeout_chain.layer_timeouts.mcpTimeoutMs;           // 默认 30000

// 链式关系：questionTimeoutMs(120000) ≥ backendTimeoutMs(90000) × margin_multiplier(1.5)
// 阈值校验：每层须 ≥ 下层 × margin_multiplier，否则启动期报错
```

### TC-2：超时阈值必须从配置读取
**严重级别**：critical

所有超时阈值必须在 config 文件管理，禁止在源码中硬编码。规则文件不硬编码具体毫秒数，所有数值从 `config/coding-standards-config.md` 的 `timeout_chain` 段读取。

**为什么**：硬编码阈值在环境变化（如换 LLM provider、增加 MCP 服务器）时需要改代码，配置化则只需改配置文件。

### TC-3：超时中断必须保留已收到的部分结果
**严重级别**：critical

超时中断时，已收到的部分结果（如 SSE 流式传输的部分答案、已加载的部分工具）必须保留并展示给用户，禁止清空。

**实现模式**：
```typescript
// 前端超时后保留部分答案
function stopLoading(reason: 'user' | 'timeout') {
  if (streamingAnswer.value) {
    messages.push({
      content: `${streamingAnswer.value}\n\n[${reason === 'user' ? '已停止' : '已超时'}]`,
      // 保留已收到的 refs 和 thinking
    });
  }
  clearCurrentRound();
}
```

### TC-4：超时必须有兜底降级路径
**严重级别**：critical

超时后必须有降级路径（如跳过 MCP 工具用内置工具回答、显示"扩展工具加载失败"提示），禁止让用户卡在"正在思考"无限等待。

**为什么**：用户感知的"AI 未回复"通常是超时后无降级提示，AI 实际有回复但被丢弃。

### TC-5：超时阈值变更必须同步更新链上所有层
**严重级别**：suggestion

修改某一层超时阈值时，必须检查链上所有层的阈值是否仍满足递增关系。如降低 MCP 超时从 30s 到 10s，需同步检查前端超时是否可降低。

## 适用场景
- 多层调用链（前端 → 后端 → 第三方 → LLM）
- SSE 流式响应
- MCP 工具加载
- 任何有超时机制的异步操作

## 不适用场景
- 单层调用（无下层耗时）
- 同步操作（无超时概念）
- 资源加载无超时需求（如内存操作）

## 检查清单
- [ ] 超时阈值是否自下而上递增覆盖
- [ ] 阈值是否从 config 读取而非硬编码
- [ ] 超时中断是否保留已收到的部分结果
- [ ] 超时后是否有降级路径
- [ ] 阈值变更是否同步更新链上所有层
