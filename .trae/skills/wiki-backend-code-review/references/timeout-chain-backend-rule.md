# 超时阈值链式匹配审查规则（BR-053）

> 复盘来源：MCP 工具串行加载 2×30s=60s 刚好触发前端 60s 超时，AI 回复被丢弃。修复：改为 Promise.allSettled 并行加载，前端超时从 60s 增到 120s。根因是多层调用链超时阈值未自下而上递增覆盖——前端超时（60s）刚好等于后端 MCP 加载超时之和（2×30s=60s），无余量导致前端在后端刚完成时超时丢弃回复（TC-1~5）。
> 所有可变参数（层顺序、余量倍数、config 字段名、超时阈值）从 [config/review-config.md](../config/review-config.md) 的"超时阈值链式匹配审查参数（timeout_chain_backend）"章节读取，禁止在本规则文件硬编码具体超时值或层名。

## Trigger Keywords

timeout, setTimeout, AbortController, 超时, 阈值, chain, layer, mcpTimeoutMs, questionTimeoutMs, frontend timeout, backend timeout, mcp timeout, llm timeout, 调用链, 链式超时, margin, 余量, 递增覆盖, partial result, SSE partial, degradation, 降级路径, 硬编码超时

## Rules

### BR-053-1：多层调用链超时必须自下而上递增覆盖，每层覆盖下层耗时之和 + 余量

- **Severity**: critical
- **Description**: 多层调用链（`timeout_chain_backend.layer_order`，默认 `frontend>backend>mcp>llm`）的超时阈值必须自下而上递增——每层超时 ≥ 下层所有调用耗时之和 × `timeout_chain_backend.margin_multiplier`（默认 `1.5`）。例如：LLM 层 30s → MCP 层需 ≥ 30s × 1.5 = 45s → 后端层需 ≥ 45s × 1.5 = 67.5s → 前端层需 ≥ 67.5s × 1.5 ≈ 101s。违反此规则会导致：上层超时 < 下层耗时之和时，上层在下层刚完成时超时丢弃回复，表现为"后端日志显示成功但前端无响应"。典型反例：前端 60s = 后端 MCP 加载 2×30s=60s，无余量，前端在后端刚完成时超时。评审时确认：从 config 读取各层超时阈值，验证 `上层阈值 ≥ 下层阈值 × margin_multiplier`，且最底层（LLM）阈值有明确依据（如模型 API 文档建议的最大响应时间）。
- **Suggested fix**:

```typescript
// 错误：前端超时 60s = 后端 MCP 加载 2×30s=60s，无余量，刚完成就超时
// config: frontend.questionTimeoutMs = 60000
// config: mcp.mcpTimeoutMs = 30000  (2 个 MCP 串行 = 60s)
// ❌ 前端 60s < 后端 60s × 1.5 = 90s，无余量

// 正确：自下而上递增覆盖，每层 = 下层 × margin_multiplier（倍数从 config 读取）
// config: timeout_chain_backend.layer_order = 'frontend>backend>mcp>llm'
// config: timeout_chain_backend.margin_multiplier = 1.5
// config: timeout_chain_backend.layer_timeouts.llmTimeoutMs = 30000      // LLM 层 30s
// config: timeout_chain_backend.layer_timeouts.mcpTimeoutMs = 45000      // MCP 层 45s（≥ 30s × 1.5）
// config: timeout_chain_backend.layer_timeouts.backendTimeoutMs = 90000  // 后端层 90s（≥ 60s × 1.5，含 MCP 并行 45s + 其他 15s）
// config: timeout_chain_backend.layer_timeouts.questionTimeoutMs = 120000 // 前端层 120s（≥ 90s × 1.5 = 135s，取整 120s 实际应更高）
// 注：并行加载后 MCP 层耗时 = max(单 MCP) 而非 Σ，见 BR-052
const layerTimeouts = config.timeout_chain_backend.layer_timeouts;
const marginMultiplier = config.timeout_chain_backend.margin_multiplier;

// 验证函数：检查每层超时是否 ≥ 下层 × margin_multiplier
function verifyTimeoutChain(timeouts: Record<string, number>, layerOrder: string[]): boolean {
  for (let i = layerOrder.length - 1; i > 0; i--) {
    const lower = timeouts[`${layerOrder[i]}TimeoutMs`];
    const upper = timeouts[`${layerOrder[i - 1]}TimeoutMs`];
    if (upper < lower * marginMultiplier) {
      console.error(`超时链违规: ${layerOrder[i - 1]}(${upper}ms) < ${layerOrder[i]}(${lower}ms) × ${marginMultiplier}`);
      return false;
    }
  }
  return true;
}
```

### BR-053-2：超时阈值必须从 config 读取，禁止硬编码

- **Severity**: critical
- **Description**: 所有超时阈值（`setTimeout` 延迟、`AbortController.timeout`、`Promise.race` 超时 Promise 的延迟值）必须从 `timeout_chain_backend.config_field_pattern`（默认 `timeout_chain_backend.layer_timeouts`）对应的 config 字段读取，禁止在代码中硬编码字面量（如 `setTimeout(fn, 30000)`）。硬编码会导致：① 阈值调整时需修改多处代码，易遗漏；② 不同环境（开发/测试/生产）无法差异化配置；③ 链式超时关系无法集中验证。评审时确认：用 Grep 检索 `setTimeout`、`AbortSignal.timeout`、`Promise.race` + `setTimeout` 模式，所有超时值均通过 config 引用而非字面量。
- **Suggested fix**:

```typescript
// 错误：硬编码超时阈值，环境切换时需改代码
const timeoutPromise = new Promise((_, reject) =>
  setTimeout(reject, 30000) // ❌ 字面量 30000
);
const controller = new AbortController();
setTimeout(() => controller.abort(), 60000); // ❌ 字面量 60000

// 正确：从 config 读取超时阈值（字段名从 config 读取）
// config: timeout_chain_backend.layer_timeouts.mcpTimeoutMs = 30000
// config: timeout_chain_backend.layer_timeouts.questionTimeoutMs = 120000
const mcpTimeoutMs = config.timeout_chain_backend.layer_timeouts.mcpTimeoutMs;
const questionTimeoutMs = config.timeout_chain_backend.layer_timeouts.questionTimeoutMs;

const timeoutPromise = new Promise((_, reject) =>
  setTimeout(reject, mcpTimeoutMs) // ✅ 从 config 读取
);
const controller = new AbortController();
setTimeout(() => controller.abort(), questionTimeoutMs); // ✅ 从 config 读取
```
### BR-053-3：超时中断必须保留已收到的部分结果，禁止清空

- **Severity**: critical
- **Description**: 超时中断时必须保留已收到的部分结果（`timeout_chain_backend.partial_result_preservation_required`，默认 `true`），禁止清空已累积的响应。典型场景：SSE 流式输出中前端超时，已收到的部分 AI 回复必须保留显示给用户，而非清空返回空——用户看到"部分回答 + 超时提示"远优于"空白 + 超时错误"。实现方式：① 前端 SSE 消费端用累积缓冲区，超时时保留已收到的 chunk；② 后端 LLM 调用超时时，已收到的 token 流必须返回给客户端；③ 禁止在 catch 块中执行 `setState('')` 清空已累积内容。评审时确认：超时 catch 块内无清空操作（如 `setMessages([])`、`setContent('')`、`state = {}`），已累积的部分结果被保留。
- **Suggested fix**:

```typescript
// 错误：SSE 超时时清空已收到的部分回复
let sseContent = '';
try {
  for await (const event of sseStream) {
    sseContent += event.data;
  }
} catch (err) {
  if (err.name === 'TimeoutError') {
    setContent(''); // ❌ 清空已收到的部分回复
    setError('请求超时');
  }
}

// 正确：超时保留已收到的部分回复（partial_result_preservation_required = true）
let sseContent = '';
try {
  for await (const event of sseStream) {
    sseContent += event.data;
  }
} catch (err) {
  if (err.name === 'TimeoutError') {
    // ✅ 保留已收到的部分回复，附加超时提示
    if (sseContent) {
      setContent(sseContent + '\n\n[请求超时，以上为部分回复]');
    } else {
      setContent('[请求超时，未收到回复]');
    }
    console.warn('[SSE] 超时，保留部分回复:', sseContent.length, '字符');
  }
}
```

### BR-053-4：超时后必须有降级路径，禁止无限等待

- **Severity**: critical
- **Description**: 超时后必须有降级路径（`timeout_chain_backend.degradation_path_required`，默认 `true`），禁止无限等待或直接抛错终止流程。典型降级路径：① MCP 工具加载超时 → 跳过 MCP 用内置工具回答（"MCP 工具暂不可用，使用内置能力回答"）；② LLM 调用超时 → 返回缓存结果或友好错误提示；③ 外部 API 超时 → 降级到本地数据源。降级路径必须：① 在 config 中配置降级策略（如 `degradation_strategy: fallback_to_builtin`）；② 日志记录降级事件供运维监控；③ 向用户明确提示当前为降级模式。评审时确认：超时 catch 块内有降级逻辑（调用 fallback 函数、返回默认值、切换数据源），而非仅 `throw err` 或空 return。
- **Suggested fix**:

```typescript
// 错误：超时后直接抛错，无降级路径，用户体验中断
try {
  const mcpTools = await loadMcpToolsWithTimeout(mcpServers);
  const result = await callLLMWithTools(query, mcpTools);
  return result;
} catch (err) {
  if (err.name === 'TimeoutError') {
    throw err; // ❌ 无降级，用户看到 500 错误
  }
}

// 正确：超时后降级到内置工具（degradation_path_required = true）
try {
  const mcpTools = await loadMcpToolsWithTimeout(mcpServers);
  const result = await callLLMWithTools(query, mcpTools);
  return result;
} catch (err) {
  if (err.name === 'TimeoutError') {
    // ✅ 降级：跳过 MCP 用内置工具回答
    console.warn('[Query] MCP 加载超时，降级到内置工具:', err.message);
    const builtinResult = await callLLMBuiltin(query);
    return {
      ...builtinResult,
      degraded: true,
      degradationReason: 'MCP 工具加载超时，使用内置能力回答'
    }; // ✅ 用户感知降级而非中断
  }
  throw err; // 非超时错误继续抛出
}
```

### BR-053-5：阈值变更必须同步检查链上所有层

- **Severity**: suggestion
- **Description**: 修改任一层超时阈值时必须同步检查链上所有层（`timeout_chain_backend.layer_order`）的覆盖关系，确认 `上层 ≥ 下层 × margin_multiplier` 仍然成立。典型遗漏：单独调高 MCP 层超时（如 30s → 60s）但未同步调高前端超时（仍 60s），导致前端超时 < MCP 超时，回复再次被丢弃。建议在 config 文件注释中标注链式依赖关系（如 `# mcpTimeoutMs 变更时须同步检查 questionTimeoutMs ≥ mcpTimeoutMs × 1.5`），或在 CI 中加入链式超时验证脚本。评审时确认：config 中超时阈值变更的 PR 描述或注释中提及"已检查链上所有层覆盖关系"。
- **Suggested fix**:

```typescript
// 错误：单独调高 MCP 超时未同步调高前端超时
// config.json 变更：
// "mcpTimeoutMs": 60000  // 30s → 60s（调高）
// "questionTimeoutMs": 60000  // ❌ 仍 60s，前端 < MCP × 1.5 = 90s

// 正确：同步调整链上所有层，保持覆盖关系
// config.json 变更（注释标注链式依赖）：
// config: timeout_chain_backend.layer_timeouts.mcpTimeoutMs = 60000      // 调高：30s → 60s
// config: timeout_chain_backend.layer_timeouts.backendTimeoutMs = 90000  // 同步：≥ 60s × 1.5 = 90s
// config: timeout_chain_backend.layer_timeouts.questionTimeoutMs = 135000 // 同步：≥ 90s × 1.5 = 135s
// 注：mcpTimeoutMs 变更时须同步检查 questionTimeoutMs ≥ mcpTimeoutMs × margin_multiplier

// CI 验证脚本示例（在 config 变更时自动检查链式覆盖）
function verifyTimeoutChainOnConfigChange(config: Config): string[] {
  const errors: string[] = [];
  const layerOrder = config.timeout_chain_backend.layer_order.split('>');
  const timeouts = config.timeout_chain_backend.layer_timeouts;
  const margin = config.timeout_chain_backend.margin_multiplier;
  for (let i = layerOrder.length - 1; i > 0; i--) {
    const lowerKey = `${layerOrder[i].toLowerCase()}TimeoutMs`;
    const upperKey = `${layerOrder[i - 1].toLowerCase()}TimeoutMs`;
    const lower = timeouts[lowerKey];
    const upper = timeouts[upperKey];
    if (upper < lower * margin) {
      errors.push(`${upperKey}(${upper}) < ${lowerKey}(${lower}) × ${margin}`);
    }
  }
  return errors;
}
```
## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `timeout_chain_backend.enabled` | `true` | 是否启用本组规则（BR-053） |
| `timeout_chain_backend.severity_br053_1` | `critical` | BR-053-1 链式覆盖违规严重级别 |
| `timeout_chain_backend.severity_br053_2` | `critical` | BR-053-2 硬编码超时违规严重级别 |
| `timeout_chain_backend.severity_br053_3` | `critical` | BR-053-3 清空部分结果违规严重级别 |
| `timeout_chain_backend.severity_br053_4` | `critical` | BR-053-4 无降级路径违规严重级别 |
| `timeout_chain_backend.severity_br053_5` | `suggestion` | BR-053-5 阈值变更未检查链上层级违规严重级别 |
| `timeout_chain_backend.layer_order` | `frontend>backend>mcp>llm` | 调用链层顺序（从上到下，`>` 分隔） |
| `timeout_chain_backend.margin_multiplier` | `1.5` | 余量倍数（每层 ≥ 下层 × 此倍数） |
| `timeout_chain_backend.config_field_pattern` | `timeout_chain_backend.layer_timeouts` | config 中超时阈值字段的命名模式 |
| `timeout_chain_backend.partial_result_preservation_required` | `true` | 超时是否必须保留部分结果 |
| `timeout_chain_backend.degradation_path_required` | `true` | 超时后是否必须有降级路径 |
| `timeout_chain_backend.layer_timeouts.llmTimeoutMs` | `30000` | LLM 层超时（毫秒） |
| `timeout_chain_backend.layer_timeouts.mcpTimeoutMs` | `30000` | MCP 层超时（毫秒） |
| `timeout_chain_backend.layer_timeouts.backendTimeoutMs` | `90000` | 后端层超时（毫秒） |
| `timeout_chain_backend.layer_timeouts.questionTimeoutMs` | `120000` | 前端层超时（毫秒） |

## 检查方式

1. 用 Grep 在 `api/` 和 `frontend/src/` 目录检索 `setTimeout`、`AbortSignal.timeout`、`AbortController` + `setTimeout`、`Promise.race` + `setTimeout` 关键字，定位所有超时设置点。
2. **BR-053-1 检查**：从 config 读取 `layer_timeouts` 各层超时值，验证链式覆盖关系：
   - `上层 ≥ 下层 × margin_multiplier` → 通过
   - 任一 `上层 < 下层 × margin_multiplier` → **BR-053-1 违规**（链式覆盖不满足）
   - 特别关注：前端超时 = 后端耗时之和（无余量）→ **BR-053-1 违规**（典型反例）
3. **BR-053-2 检查**：用 Grep 检索超时设置代码中的字面量数字：
   - `setTimeout(fn, 30000)` 字面量 → **BR-053-2 违规**（应从 config 读取）
   - `setTimeout(fn, config.xxx.timeoutMs)` 从 config 读取 → 通过
   - `AbortSignal.timeout(30000)` 字面量 → **BR-053-2 违规**
4. **BR-053-3 检查**：用 Grep 检索超时 catch 块内的清空操作：
   - catch 块内有 `setContent('')`、`setMessages([])`、`state = {}` 等清空 → **BR-053-3 违规**（清空部分结果）
   - catch 块内保留已累积变量 → 通过
   - catch 块内 `setContent(sseContent + ...)` 附加提示 → 通过
5. **BR-053-4 检查**：用 Grep 检索超时 catch 块内的降级逻辑：
   - catch 块内仅 `throw err` 或空 return → **BR-053-4 违规**（无降级路径）
   - catch 块内调用 fallback 函数 / 返回默认值 / 切换数据源 → 通过
   - catch 块内有 `console.warn` 降级日志 → 通过
6. **BR-053-5 检查**：检查 config 文件变更历史或 PR 描述：
   - 超时阈值变更的 PR 描述未提及"已检查链上所有层" → suggestion（建议同步检查）
   - config 注释中标注链式依赖关系 → 通过
   - CI 中有链式超时验证脚本 → 通过

## 正确示例

```typescript
// config/timeout.ts —— 完整链式超时配置（从 config 读取，禁止硬编码）
import { config } from '../config/index.js';

// 从 config 读取链式超时参数
const layerOrder = config.timeout_chain_backend.layer_order.split('>'); // ['frontend','backend','mcp','llm']
const marginMultiplier = config.timeout_chain_backend.margin_multiplier; // 1.5
const layerTimeouts = config.timeout_chain_backend.layer_timeouts;
const partialResultRequired = config.timeout_chain_backend.partial_result_preservation_required;
const degradationRequired = config.timeout_chain_backend.degradation_path_required;

// 验证链式覆盖关系（启动时检查）
export function verifyTimeoutChain(): void {
  for (let i = layerOrder.length - 1; i > 0; i--) {
    const lowerKey = `${layerOrder[i].toLowerCase()}TimeoutMs`;
    const upperKey = `${layerOrder[i - 1].toLowerCase()}TimeoutMs`;
    const lower = layerTimeouts[lowerKey];
    const upper = layerTimeouts[upperKey];
    if (upper < lower * marginMultiplier) {
      throw new Error(`超时链违规: ${upperKey}(${upper}ms) < ${lowerKey}(${lower}ms) × ${marginMultiplier}`);
    }
  }
  console.log('[Timeout] 链式覆盖验证通过');
}

// services/query.ts —— 超时处理 + 降级 + 部分结果保留
export async function handleQuery(query: string): Promise<QueryResult> {
  const mcpTimeoutMs = layerTimeouts.mcpTimeoutMs;
  let partialTools: Tool[] = [];

  try {
    // MCP 加载带超时（BR-053-2: 阈值从 config 读取）
    const mcpResult = await Promise.race([
      loadAllMcpTools(mcpServers),
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new TimeoutError('MCP 加载超时')), mcpTimeoutMs)
      )
    ]);
    partialTools = mcpResult.tools;
    return await callLLMWithTools(query, partialTools);
  } catch (err) {
    if (err.name === 'TimeoutError') {
      // BR-053-4: 降级路径（跳过 MCP 用内置工具）
      console.warn('[Query] MCP 超时，降级到内置工具:', err.message);
      const builtinResult = await callLLMBuiltin(query);
      return {
        ...builtinResult,
        degraded: true,
        degradationReason: 'MCP 工具加载超时，使用内置能力回答'
      };
    }
    // BR-053-3: 非超时错误保留已收到的部分工具
    if (partialTools.length > 0 && partialResultRequired) {
      console.warn('[Query] 非超时错误，保留部分 MCP 工具:', partialTools.length);
    }
    throw err;
  }
}

// frontend/src/lib/sse.ts —— SSE 超时保留部分回复（BR-053-3）
export async function consumeSSEStreamWithTimeout(
  url: string,
  onChunk: (content: string) => void,
  timeoutMs: number
): Promise<string> {
  let accumulated = '';
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) });
    for await (const event of parseSSEStream(response.body!)) {
      accumulated += event.data;
      onChunk(accumulated);
    }
    return accumulated;
  } catch (err) {
    if (err.name === 'TimeoutError' && partialResultRequired) {
      // ✅ 保留已收到的部分回复
      console.warn('[SSE] 超时，保留部分回复:', accumulated.length, '字符');
      onChunk(accumulated + '\n\n[请求超时，以上为部分回复]');
      return accumulated;
    }
    throw err;
  }
}
```

## 错误示例

```typescript
// 错误 1：前端超时 = 后端耗时之和，无余量（BR-053-1 违规）
// config: questionTimeoutMs = 60000, mcpTimeoutMs = 30000 (2 个串行 = 60s)
// ❌ 前端 60s < 后端 60s × 1.5 = 90s

// 错误 2：硬编码超时阈值（BR-053-2 违规）
setTimeout(() => controller.abort(), 60000); // ❌ 字面量 60000
const timeoutPromise = new Promise((_, reject) => setTimeout(reject, 30000)); // ❌ 字面量 30000

// 错误 3：超时清空已收到的部分回复（BR-053-3 违规）
try {
  for await (const event of sseStream) {
    sseContent += event.data;
  }
} catch (err) {
  if (err.name === 'TimeoutError') {
    setContent(''); // ❌ 清空部分回复
  }
}

// 错误 4：超时后无降级路径（BR-053-4 违规）
try {
  const mcpTools = await loadMcpToolsWithTimeout(mcpServers);
  return await callLLMWithTools(query, mcpTools);
} catch (err) {
  if (err.name === 'TimeoutError') {
    throw err; // ❌ 无降级，用户看到 500 错误
  }
}

// 错误 5：单独调高 MCP 超时未同步调高前端（BR-053-5 违规，suggestion）
// config 变更：mcpTimeoutMs 30s → 60s，questionTimeoutMs 仍 60s
// ❌ 前端 60s < MCP 60s × 1.5 = 90s，链式覆盖被破坏

// 错误 6：超时 catch 块内仅 return 空对象（BR-053-4 违规）
catch (err) {
  if (err.name === 'TimeoutError') {
    return { tools: [], result: '' }; // ❌ 无降级路径，无日志
  }
}
```

## 适配新项目

- **Python 项目**：`setTimeout` 改为 `asyncio.wait_for(coro, timeout)`，`AbortController` 改为 `asyncio.CancelledError` 捕获；config 读取用 `pydantic-settings` 或 `python-dotenv`。
- **Go 项目**：`setTimeout` 改为 `context.WithTimeout(ctx, duration)`，`AbortController` 改为 `ctx.Done()` channel 监听；config 用 viper 或 envconfig 库。
- **Rust 项目**：`setTimeout` 改为 `tokio::time::timeout(duration, fut)`，`AbortController` 改为 `tokio::select!` + `tokio::time::sleep`；config 用 config crate 或 serde。
- **Java 项目**：`setTimeout` 改为 `CompletableFuture.orTimeout(timeout, TimeUnit)`，`AbortController` 改为 `Future.cancel(true)`；config 用 Spring `@Value` 或 `@ConfigurationProperties`。
- **单层架构项目**：若项目只有一层调用（如纯前端无后端），`layer_order` 设为 `frontend>llm`，只需验证前端超时 ≥ LLM 超时 × margin_multiplier。
- **微服务架构项目**：`layer_order` 扩展为 `gateway>service_a>service_b>llm`，每层超时独立配置；建议在网关层加入链式超时验证中间件。
- **无超时场景**：对于同步本地操作（如内存计算、本地文件读取 < 1s），可不设超时，本规则不适用；但跨进程/跨网络调用必须设超时。
- **流式响应项目**：SSE/WebSocket 流式响应的超时阈值应基于"首字节超时"（连接建立到首个 chunk）而非"总耗时"，避免长回复被误超时；`layer_timeouts` 可增加 `sseFirstByteTimeoutMs` 字段。