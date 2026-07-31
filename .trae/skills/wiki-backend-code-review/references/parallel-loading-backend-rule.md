# 多资源并行加载审查规则（BR-052）

> 复盘来源：MCP 工具串行加载（`for await` 逐个 await）导致 2 个 MCP × 30s = 60s 刚好触发前端 60s 超时，AI 回复被前端丢弃。修复方案：改为 `Promise.allSettled` 并行加载，单失败收集到 `errors` 数组不阻断整体，前端超时从 60s 调整到 120s（PL-1~5）。
> 所有可变参数（资源类型模式、必需包装器、禁止模式、错误收集字段名）从 [config/review-config.md](../config/review-config.md) 的"多资源并行加载审查参数（parallel_loading_backend）"章节读取，禁止在本规则文件硬编码具体资源名或函数名。

## Trigger Keywords

Promise.allSettled, Promise.all, for await, for...of, 串行加载, 并行加载, MCP, loadMcpTools, loadResources, fetchMultiple, errors[], source, 降级, independent resources, allSettled vs all, 资源加载, 工具加载, partial failure

## Rules

### BR-052-1：N 个独立资源加载必须用 Promise.allSettled，禁止 for await 串行

- **Severity**: critical
- **Description**: 当同时加载 N 个相互独立的资源（`parallel_loading_backend.independent_resource_patterns`，默认 `MCP/API/file`，如 MCP 工具列表、外部 API 配置、磁盘配置文件）时，必须用 `parallel_loading_backend.required_wrapper`（默认 `Promise.allSettled`）并行加载，禁止用 `for await` / `for...of` + `await` 串行加载。串行加载会导致总耗时 = Σ(单资源耗时)，N 个资源各 30s 时总耗时 = N × 30s；并行加载总耗时 ≈ max(单资源耗时) = 30s。当 N × 单资源耗时 ≥ 上层超时阈值时（如 2 × 30s = 60s ≥ 前端 60s 超时），AI 回复会被前端丢弃，表现为"后端正常返回但前端无响应"。评审时确认：检测到 `for await` / `for...of` 循环内有 `await` 加载独立资源，且资源间无依赖关系时，必须改写为 `Promise.allSettled([...])`。
- **Suggested fix**:

```typescript
// 错误：for...of 串行加载 MCP 工具，2 个 MCP × 30s = 60s 触发前端超时
const tools = [];
for (const mcp of mcpServers) {
  const tool = await loadMcpTools(mcp); // ❌ 串行 await，总耗时 = Σ(单次)
  tools.push(tool);
}

// 正确：Promise.allSettled 并行加载（wrapper 从 config 读取）
// config: parallel_loading_backend.required_wrapper = 'Promise.allSettled'
const results = await Promise.allSettled(mcpServers.map(mcp => loadMcpTools(mcp)));
const tools = results
  .filter((r): r is PromiseFulfilledResult<Tool> => r.status === 'fulfilled')
  .map(r => r.value);
```

### BR-052-2：必须用 allSettled 而非 all，单失败不阻断整体

- **Severity**: critical
- **Description**: 并行加载必须用 `parallel_loading_backend.required_wrapper`（默认 `Promise.allSettled`）而非 `Promise.all`。`Promise.all` 是"快速失败"语义——任一 Promise reject 会导致整体 reject，其他已成功的资源结果被丢弃；在资源加载场景下，单个 MCP 不可用不应阻断其他可用 MCP 的工具加载。`Promise.allSettled` 等待所有 Promise 完成（fulfilled 或 rejected），单失败由调用方收集到 `errors` 数组降级处理。评审时确认：并行加载代码用的是 `Promise.allSettled` 而非 `Promise.all`；若用 `Promise.all`，必须有显式注释说明"资源间强依赖，单失败需整体回滚"（如事务场景），否则视为违规。
- **Suggested fix**:

```typescript
// 错误：Promise.all 单失败整体 reject，其他 MCP 工具被丢弃
try {
  const tools = await Promise.all(mcpServers.map(mcp => loadMcpTools(mcp))); // ❌ 任一失败全部丢弃
  return { tools };
} catch (err) {
  return { tools: [], error: err.message }; // ❌ 一个 MCP 不可用导致全部不可用
}

// 正确：Promise.allSettled 单失败不阻断，部分结果仍可用
const results = await Promise.allSettled(mcpServers.map(mcp => loadMcpTools(mcp)));
const tools: Tool[] = [];
const errors: LoadError[] = [];
for (const r of results) {
  if (r.status === 'fulfilled') tools.push(...r.value);
  else errors.push({ source: r.reason.source, message: r.reason.message }); // ✅ 单失败收集
}
return { tools, errors }; // ✅ 部分 MCP 不可用时仍返回可用工具
```
### BR-052-3：失败结果必须收集到 errors 数组含 source 字段，降级处理

- **Severity**: critical
- **Description**: `Promise.allSettled` 返回的 rejected 结果必须收集到 `parallel_loading_backend.error_collection_field`（默认 `errors`）数组中，每个错误对象必须包含 `parallel_loading_backend.error_source_field`（默认 `source`）字段标识失败来源（如 MCP 名称、API endpoint、文件路径），便于上层定位"哪个资源失败"与降级处理。降级处理指：① 跳过失败资源继续返回其他成功资源的结果；② 在响应中附带 `errors` 数组让上层感知部分失败；③ 日志记录失败详情供运维排查。禁止直接吞掉 rejected 结果（如 `results.filter(r => r.status === 'fulfilled')` 丢弃 rejected），否则单失败会无声丢失，运维无法定位。评审时确认：并行加载后的处理代码包含 `errors` 数组收集逻辑，且每个 error 对象有 `source` 字段。
- **Suggested fix**:

```typescript
// 错误：rejected 结果被静默丢弃，运维无法定位失败资源
const results = await Promise.allSettled(mcpServers.map(mcp => loadMcpTools(mcp)));
const tools = results
  .filter((r): r is PromiseFulfilledResult<Tool[]> => r.status === 'fulfilled')
  .flatMap(r => r.value); // ❌ rejected 结果被丢弃，无 errors 数组

// 正确：rejected 收集到 errors 数组，含 source 字段（字段名从 config 读取）
// config: parallel_loading_backend.error_collection_field = 'errors'
// config: parallel_loading_backend.error_source_field = 'source'
const results = await Promise.allSettled(
  mcpServers.map(async mcp => {
    try {
      return { source: mcp.name, tools: await loadMcpTools(mcp) };
    } catch (err) {
      // 抛出含 source 的错误对象，便于 rejected 分支定位来源
      throw { source: mcp.name, message: err.message, original: err };
    }
  })
);
const tools: Tool[] = [];
const errors: Array<{ source: string; message: string }> = [];
for (const r of results) {
  if (r.status === 'fulfilled') tools.push(...r.value.tools);
  else errors.push({ source: r.reason.source, message: r.reason.message }); // ✅ 含 source
}
if (errors.length > 0) {
  console.warn('[loadMcpTools] 部分资源加载失败:', errors); // ✅ 降级日志
}
return { tools, errors }; // ✅ 上层感知部分失败
```

### BR-052-4：同一资源内子任务可同步处理，并行层级聚焦资源粒度

- **Severity**: best-practice
- **Description**: 并行加载的粒度聚焦在"独立资源"层级（如多个 MCP server、多个 API endpoint、多个配置文件），同一资源内部的子任务（如单个 MCP 内的多个工具列表初始化、单个 API 的鉴权 + 数据拉取）可以同步串行处理，无需强行并行化。过度并行化会：① 增加代码复杂度（错误处理路径指数增长）；② 触发下游限流（如同一 API 的并发请求被限流）；③ 增加调试难度（并发竞态难以复现）。评审时确认：并行加载只用在"资源间相互独立"的场景，资源内部子任务用 `await` 串行即可；若发现资源内部子任务也被强行 `Promise.allSettled` 包裹，建议简化（best-practice 级，非强制）。
- **Suggested fix**:

```typescript
// 过度并行化：单个 MCP 内部的鉴权 + 工具列表加载被强行并行（增加复杂度无收益）
async function loadMcpTools(mcp: McpServer): Promise<Tool[]> {
  const [auth, tools] = await Promise.allSettled([  // ❌ 鉴权与工具加载有依赖关系，不应并行
    authenticate(mcp),
    listTools(mcp) // 未鉴权时调用会失败
  ]);
  // ...处理竞态与错误组合，代码复杂
}

// 正确：资源内部子任务串行，资源间并行（粒度聚焦资源层级）
async function loadMcpTools(mcp: McpServer): Promise<Tool[]> {
  const token = await authenticate(mcp);    // ✅ 子任务串行
  const tools = await listTools(mcp, token); // ✅ 子任务串行
  return tools;
}
// 资源间并行（在调用方）
const results = await Promise.allSettled(mcpServers.map(mcp => loadMcpTools(mcp)));
```

### BR-052-5：并行加载必须有总超时兜底防止永久挂起

- **Severity**: suggestion
- **Description**: 并行加载必须有 `parallel_loading_backend.total_timeout_required`（默认 `true`）的总超时兜底，防止某个资源因网络挂起或下游不可达导致 `Promise.allSettled` 永久等待。总超时用 `Promise.race([Promise.allSettled([...]), timeoutPromise(totalTimeoutMs)])` 实现，超时后返回已收到的部分结果（结合 BR-052-3 的 errors 数组）。总超时阈值从 config 读取（见 `timeout_chain_backend` 章节），禁止硬编码。评审时确认：并行加载代码有总超时兜底，超时后返回部分结果而非整体 reject。
- **Suggested fix**:

```typescript
// 错误：无总超时兜底，某个 MCP 挂起导致 Promise.allSettled 永久等待
const results = await Promise.allSettled(
  mcpServers.map(mcp => loadMcpTools(mcp)) // ❌ 无超时，永久挂起风险
);

// 正确：Promise.race 总超时兜底，超时返回部分结果（阈值从 config 读取）
// config: timeout_chain_backend.layer_timeouts.mcpTimeoutMs = 30000
const totalTimeoutMs = config.timeout_chain_backend.layer_timeouts.mcpTimeoutMs;
const timeoutPromise = new Promise<never>((_, reject) =>
  setTimeout(() => reject(new Error('MCP 并行加载总超时')), totalTimeoutMs)
);

let results: PromiseSettledResult<Tool[]>[];
try {
  results = await Promise.race([
    Promise.allSettled(mcpServers.map(mcp => loadMcpTools(mcp))),
    timeoutPromise
  ]);
} catch (err) {
  // 超时：返回已收到的部分结果（结合 errors 数组降级）
  console.warn('[loadMcpTools] 并行加载超时，返回空列表降级:', err.message);
  return { tools: [], errors: [{ source: 'parallel-loader', message: err.message }] };
}
// ...正常处理 results
```
## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `parallel_loading_backend.enabled` | `true` | 是否启用本组规则（BR-052） |
| `parallel_loading_backend.severity_br052_1` | `critical` | BR-052-1 串行加载违规严重级别 |
| `parallel_loading_backend.severity_br052_2` | `critical` | BR-052-2 用 Promise.all 违规严重级别 |
| `parallel_loading_backend.severity_br052_3` | `critical` | BR-052-3 错误收集缺失违规严重级别 |
| `parallel_loading_backend.severity_br052_4` | `best-practice` | BR-052-4 过度并行化违规严重级别 |
| `parallel_loading_backend.severity_br052_5` | `suggestion` | BR-052-5 总超时兜底缺失违规严重级别 |
| `parallel_loading_backend.independent_resource_patterns` | `MCP,API,file` | 独立资源类型模式（逗号分隔，用于识别需并行加载的场景） |
| `parallel_loading_backend.required_wrapper` | `Promise.allSettled` | 必需的并行加载包装器 |
| `parallel_loading_backend.forbidden_patterns` | `for await,for...of,serial` | 禁用的串行加载模式（逗号分隔） |
| `parallel_loading_backend.error_collection_required` | `true` | 是否必须收集 rejected 到 errors 数组 |
| `parallel_loading_backend.error_collection_field` | `errors` | 错误收集字段名 |
| `parallel_loading_backend.error_source_field` | `source` | 错误对象中标识来源的字段名 |
| `parallel_loading_backend.total_timeout_required` | `true` | 是否必须配置总超时兜底 |

## 检查方式

1. 用 Grep 在 `api/` 目录检索 `for await`、`for...of` + 循环体内 `await` 关键字组合，定位所有串行资源加载调用点。
2. **BR-052-1 检查**：对每个串行加载调用点，确认加载的资源是否相互独立：
   - 资源间无依赖关系（如多个 MCP、多个 API endpoint）且用 `for await` / `for...of` 串行 → **BR-052-1 违规**（应用 Promise.allSettled）
   - 资源间有依赖关系（如鉴权后才能加载工具）→ 通过（子任务串行合理，见 BR-052-4）
3. **BR-052-2 检查**：用 Grep 检索 `Promise.all` 调用：
   - 用于独立资源加载且无"强依赖"注释 → **BR-052-2 违规**（应用 allSettled）
   - 用于事务/强依赖场景且有注释说明 → 通过
4. **BR-052-3 检查**：用 Grep 检索 `Promise.allSettled` 后的处理代码：
   - 有 `filter(r => r.status === 'fulfilled')` 但无 `errors` 数组收集 rejected → **BR-052-3 违规**（错误被静默丢弃）
   - 有 `errors` 数组且每个 error 对象含 `source` 字段 → 通过
   - 有 `errors` 数组但 error 对象无 `source` 字段 → suggestion（建议补充 source 便于定位）
5. **BR-052-4 检查**：用 Grep 检索资源内部子任务是否被强行并行：
   - 单个资源内部用 `Promise.allSettled` 包裹子任务且有依赖关系 → suggestion（建议简化为串行）
   - 资源内部子任务串行 + 资源间并行 → 通过
6. **BR-052-5 检查**：用 Grep 检索 `Promise.allSettled` 调用是否有 `Promise.race` 总超时兜底：
   - 有 `Promise.race` + 超时阈值从 config 读取 → 通过
   - 无总超时兜底 → suggestion（建议增加超时防止永久挂起）
   - 有总超时但阈值硬编码 → suggestion（建议从 config 读取）

## 正确示例

```typescript
// services/mcp-loader.ts —— 完整合规实现
import { config } from '../config/index.js';

// 从 config 读取参数（禁止硬编码）
const requiredWrapper = config.parallel_loading_backend.required_wrapper; // 'Promise.allSettled'
const errorCollectionField = config.parallel_loading_backend.error_collection_field; // 'errors'
const errorSourceField = config.parallel_loading_backend.error_source_field; // 'source'
const totalTimeoutMs = config.timeout_chain_backend.layer_timeouts.mcpTimeoutMs; // 30000

interface LoadResult {
  tools: Tool[];
  errors: Array<{ source: string; message: string }>;
}

export async function loadAllMcpTools(mcpServers: McpServer[]): Promise<LoadResult> {
  // 1. 单个 MCP 内部子任务串行（BR-052-4）：鉴权 → 列表加载
  async function loadSingleMcp(mcp: McpServer): Promise<Tool[]> {
    const token = await authenticate(mcp);
    const tools = await listTools(mcp, token);
    return tools;
  }

  // 2. 资源间并行 + 总超时兜底（BR-052-1, BR-052-5）
  const timeoutPromise = new Promise<never>((_, reject) =>
    setTimeout(() => reject(new Error('MCP 并行加载总超时')), totalTimeoutMs)
  );

  let results: PromiseSettledResult<Tool[]>[];
  try {
    results = await Promise.race([
      Promise.allSettled(mcpServers.map(mcp =>
        loadSingleMcp(mcp).catch(err => {
          // 抛出含 source 的错误对象（BR-052-3）
          throw { [errorSourceField]: mcp.name, message: err.message, original: err };
        })
      )),
      timeoutPromise
    ]);
  } catch (err: any) {
    // 超时降级：返回空工具列表 + 错误信息
    console.warn('[loadAllMcpTools] 并行加载超时，降级返回空列表:', err.message);
    return {
      tools: [],
      [errorCollectionField]: [{ [errorSourceField]: 'parallel-loader', message: err.message }]
    } as LoadResult;
  }

  // 3. 失败结果收集到 errors 数组（BR-052-2, BR-052-3）
  const tools: Tool[] = [];
  const errors: Array<{ source: string; message: string }> = [];
  for (const r of results) {
    if (r.status === 'fulfilled') {
      tools.push(...r.value);
    } else {
      errors.push({
        source: r.reason[errorSourceField] ?? 'unknown',
        message: r.reason.message ?? String(r.reason)
      });
      console.warn(`[loadAllMcpTools] MCP 加载失败:`, r.reason); // 降级日志
    }
  }

  return { tools, [errorCollectionField]: errors } as LoadResult;
}
```

## 错误示例

```typescript
// 错误 1：for...of 串行加载独立 MCP（BR-052-1 违规）
const tools = [];
for (const mcp of mcpServers) {
  const tool = await loadMcpTools(mcp); // ❌ 串行，2×30s=60s 触发前端超时
  tools.push(tool);
}

// 错误 2：用 Promise.all 单失败整体 reject（BR-052-2 违规）
try {
  const tools = await Promise.all(mcpServers.map(mcp => loadMcpTools(mcp))); // ❌ 一个失败全丢弃
} catch (err) {
  return { tools: [] }; // ❌ 其他 MCP 工具被连坐
}

// 错误 3：rejected 结果被静默丢弃（BR-052-3 违规）
const results = await Promise.allSettled(mcpServers.map(mcp => loadMcpTools(mcp)));
const tools = results
  .filter(r => r.status === 'fulfilled')
  .flatMap(r => r.value); // ❌ rejected 丢失，运维无法定位

// 错误 4：errors 数组无 source 字段（BR-052-3 部分违规，suggestion）
const errors = results
  .filter(r => r.status === 'rejected')
  .map(r => ({ message: r.reason.message })); // ❌ 缺 source，无法定位失败资源

// 错误 5：资源内部子任务强行并行（BR-052-4 违规，best-practice）
async function loadMcpTools(mcp: McpServer) {
  const [auth, tools] = await Promise.allSettled([  // ❌ 鉴权与列表加载有依赖
    authenticate(mcp), listTools(mcp) // listTools 未鉴权会失败
  ]);
}

// 错误 6：无总超时兜底（BR-052-5 违规，suggestion）
const results = await Promise.allSettled(
  mcpServers.map(mcp => loadMcpTools(mcp)) // ❌ 某 MCP 挂起导致永久等待
);

// 错误 7：总超时阈值硬编码（BR-052-5 部分违规，suggestion）
const results = await Promise.race([
  Promise.allSettled(mcpServers.map(mcp => loadMcpTools(mcp))),
  new Promise((_, reject) => setTimeout(reject, 30000)) // ❌ 阈值硬编码，应从 config 读取
]);
```

## 适配新项目

- **Python 项目**：`required_wrapper` 改为 `asyncio.gather(return_exceptions=True)`，`for await` 改为 `async for`；错误收集用 `[r for r in results if isinstance(r, Exception)]`。
- **Go 项目**：`required_wrapper` 改为 `errgroup.Group` + `g.Go(...)`，单 goroutine 失败不阻断其他；错误收集用 `[]error` 切片。
- **Rust 项目**：`required_wrapper` 改为 `futures::future::join_all` 或 `tokio::task::JoinSet`，错误用 `Result<Vec<T>, Vec<E>>` 收集。
- **Java 项目**：`required_wrapper` 改为 `CompletableFuture.allOf(...).exceptionally(...)`，错误用 `List<Throwable>` 收集。
- **强依赖事务场景**：若资源间确实强依赖（如分布式事务），允许用 `Promise.all` 但必须在代码注释中说明"事务回滚语义"，评审时确认注释存在。
- **单资源场景**：若只有一个资源加载（N=1），并行化无意义，`await loadResource()` 即可，本规则不适用。
- **流式加载场景**：若资源是 AsyncIterable 流式加载（如 SSE 事件流），`for await` 是合理用法，本规则不适用；并行化仅在"批量加载多个独立资源"场景生效。