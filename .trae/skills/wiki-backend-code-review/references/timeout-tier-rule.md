# 超时分级策略审查规则（BR-055）

> 复盘来源：v3 媒体生成工具开发中，视频创建任务、视频轮询、图像生成、视频下载、LLM 单轮调用五类操作的预估耗时差异巨大（秒级 → 分钟级），统一用一个超时值会导致：①短任务超时过长，失败时用户等待过久；②长任务超时过短，正常请求被误判超时（CODING-057）。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"超时分级策略审查参数（timeout_tier）"章节读取，禁止在本规则文件硬编码超时毫秒数。

## Trigger Keywords

AbortSignal.timeout, setTimeout, signal:, timeout, task_creation, task_polling, image_generation, video_download, llm_small, llm_large, proxy_overhead_ms, tokenBudget, 超时, 分级, 字面量, 硬编码超时

## Rules

### BR-055-1：调用外部 API 必须按预估耗时分级设置超时，禁止所有调用用同一超时值

- **Severity**: critical
- **Description**: 调用外部 API 或长任务时必须按预估耗时分级设置 `AbortSignal.timeout`，从 `timeout_tier.timeout_tiers` 读取分级值。统一用一个超时值会导致：①短任务超时过长，失败时用户等待过久；②长任务超时过短，正常请求被误判超时。必须包含 6 个分级：`task_creation`（30s）/ `task_polling`（30s）/ `image_generation`（60s）/ `video_download`（120s）/ `llm_small`（60s）/ `llm_large`（180s）。评审时确认：业务代码中 `AbortSignal.timeout(xxx)` 的 xxx 从 config 读取且分级匹配调用类型。
- **Suggested fix**:

```typescript
// 错误：所有调用用同一超时值（30s）
await fetch(url, { signal: AbortSignal.timeout(30000) }); // ❌ 视频下载需 120s，30s 会误判超时
await fetch(url, { signal: AbortSignal.timeout(30000) }); // ❌ 任务创建只需 1s，30s 失败时用户等待过久

// 正确：按预估耗时分级设置（分级值从 config 读取）
const tiers = config.timeout_tier.timeout_tiers;
await fetch(url, { signal: AbortSignal.timeout(tiers.task_creation) });   // ✅ 30s
await fetch(url, { signal: AbortSignal.timeout(tiers.video_download) }); // ✅ 120s
```

### BR-055-2：超时阈值必须从 config 读取，禁止字面量硬编码

- **Severity**: critical
- **Description**: 所有 `AbortSignal.timeout(xxx)` 和 `setTimeout(fn, xxx)` 中的超时值必须从 `timeout_tier.timeout_tiers` 读取，禁止在代码中硬编码字面量数字（如 `30000` / `60000`）。硬编码超时值无法通过配置调整，环境变化（如代理场景需加宽超时）时需改代码重新部署。评审时确认：超时设置代码中无字面量数字，均从 config 引用。
- **Suggested fix**:

```typescript
// 错误：字面量硬编码超时值
await fetch(url, { signal: AbortSignal.timeout(60000) }); // ❌ 应从 config.timeout_tier.timeout_tiers 读取

// 正确：从 config 读取
const tiers = config.timeout_tier.timeout_tiers;
await fetch(url, { signal: AbortSignal.timeout(tiers.image_generation) }); // ✅
```

### BR-055-3：调用类型与超时分级必须匹配，禁止混用

- **Severity**: critical
- **Description**: 调用类型与超时分级必须匹配——创建任务用 `task_creation`，轮询用 `task_polling`，图像生成用 `image_generation`，视频下载用 `video_download`，LLM 调用按 tokenBudget 选 `llm_small` 或 `llm_large`。混用会导致短任务用过长超时（用户等待久）或长任务用过短超时（误判超时）。评审时确认：每个 `AbortSignal.timeout` 使用的分级与调用类型语义匹配。
- **Suggested fix**:

```typescript
// 错误：任务创建用 video_download 超时（120s），失败时用户等待过久
const createResp = await fetchWithDiagnostics(`${baseUrl}/videos`, {
  signal: AbortSignal.timeout(tiers.video_download), // ❌ 创建任务应秒级返回，用 120s 超时过长
});

// 正确：任务创建用 task_creation 超时（30s）
const createResp = await fetchWithDiagnostics(`${baseUrl}/videos`, {
  signal: AbortSignal.timeout(tiers.task_creation), // ✅ 30s，应秒级返回
});
```

### BR-055-4：LLM 调用必须按 tokenBudget 分级，禁止统一用一个值

- **Severity**: suggestion
- **Description**: LLM 调用必须按 `tokenBudget` 选择 `llm_small`（4k token，默认 60s）或 `llm_large`（16k token，默认 180s），禁止统一用一个超时值。16k token 的 PPT 生成需 180s，统一用 60s 会超时；4k token 的普通问答用 180s 则失败时用户等待过久。评审时确认：LLM 调用的超时设置有 tokenBudget 条件分支。
- **Suggested fix**:

```typescript
// 错误：LLM 调用不按 tokenBudget 分级
const harness = new Harness({ timeout: 60000 }); // ❌ 16k token 的 PPT 生成需 180s，60s 会超时

// 正确：按 tokenBudget 分级
const tiers = config.timeout_tier.timeout_tiers;
const llmTimeout = harnessConfig.budget.tokenBudget <= 4000 ? tiers.llm_small : tiers.llm_large;
const harness = new Harness({ ...harnessConfig, timeout: llmTimeout }); // ✅
```

### BR-055-5：代理场景必须考虑 proxy_overhead_ms 加宽超时

- **Severity**: suggestion
- **Description**: 通过 HTTPS_PROXY 访问外部 API 时，代理可能增加 10-20s 延迟，超时需考虑 `timeout_tier.proxy_overhead_ms`（默认 20000ms）加宽。未加宽会导致代理场景下正常请求被误判超时。评审时确认：通过代理访问外部 API 的超时设置考虑了代理开销。
- **Suggested fix**:

```typescript
// 错误：代理场景未加宽超时
const proxyAgent = new ProxyAgent(process.env.HTTPS_PROXY!);
const resp = await fetchWithDiagnostics(url, {
  dispatcher: proxyAgent,
  signal: AbortSignal.timeout(tiers.image_generation), // ❌ 代理增加 10-20s 延迟，60s 可能不够
});

// 正确：代理场景加宽超时
const proxyOverhead = config.timeout_tier.proxy_overhead_ms;
const resp = await fetchWithDiagnostics(url, {
  dispatcher: proxyAgent,
  signal: AbortSignal.timeout(tiers.image_generation + proxyOverhead), // ✅ 80s
});
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `timeout_tier.enabled` | `true` | 是否启用本组规则（BR-055） |
| `timeout_tier.severity_br055_1` | `critical` | BR-055-1 统一超时违规严重级别 |
| `timeout_tier.severity_br055_2` | `critical` | BR-055-2 硬编码超时违规严重级别 |
| `timeout_tier.severity_br055_3` | `critical` | BR-055-3 分级混用违规严重级别 |
| `timeout_tier.severity_br055_4` | `suggestion` | BR-055-4 LLM 未分级违规严重级别 |
| `timeout_tier.severity_br055_5` | `suggestion` | BR-055-5 代理未加宽违规严重级别 |
| `timeout_tier.timeout_tiers.task_creation` | `30000` | 任务创建超时（毫秒） |
| `timeout_tier.timeout_tiers.task_polling` | `30000` | 任务轮询超时（毫秒） |
| `timeout_tier.timeout_tiers.image_generation` | `60000` | 图像生成超时（毫秒） |
| `timeout_tier.timeout_tiers.video_download` | `120000` | 视频下载超时（毫秒） |
| `timeout_tier.timeout_tiers.llm_small` | `60000` | LLM 小 token 预算超时（4k token） |
| `timeout_tier.timeout_tiers.llm_large` | `180000` | LLM 大 token 预算超时（16k token） |
| `timeout_tier.proxy_overhead_ms` | `20000` | 代理额外开销（毫秒） |
| `timeout_tier.llm_small_token_threshold` | `4000` | llm_small 适用 token 上限 |
| `timeout_tier.llm_large_token_threshold` | `16000` | llm_large 适用 token 上限 |

## 检查方式

1. **分级配置检查**：用 Grep 检索 config 文件，确认 `timeout_tier.timeout_tiers` 含 6 个分级（task_creation / task_polling / image_generation / video_download / llm_small / llm_large）。缺失分级 → **BR-055-1 违规**。
2. **字面量硬编码检查**：用 Grep 在 `api/src/` 目录检索 `AbortSignal.timeout(` 和 `setTimeout(` 调用，参数为字面量数字（如 `30000` / `60000`）→ **BR-055-2 违规**。
3. **分级匹配检查**：对每个 `AbortSignal.timeout(tiers.xxx)` 调用，确认 xxx 与调用类型语义匹配：
   - 创建任务用 task_creation → 通过
   - 创建任务用 video_download → **BR-055-3 违规**（分级混用）
4. **LLM tokenBudget 检查**：用 Grep 检索 LLM 调用的超时设置，确认有 tokenBudget 条件分支选择 llm_small / llm_large。统一用一个值 → **BR-055-4 违规**（suggestion）。
5. **代理场景检查**：用 Grep 检索 `ProxyAgent` / `HTTPS_PROXY` 用法，确认超时设置考虑了 `proxy_overhead_ms` 加宽。未加宽 → **BR-055-5 违规**（suggestion）。

## 正确示例

```typescript
// services/api/src/workflows/media-generation-workflow.ts
import { config } from '../config.js';

const tiers = config.timeout_tier.timeout_tiers;

// ✅ 任务创建：30s（应秒级返回）
const createResp = await fetchWithDiagnostics(`${baseUrl}/videos`, {
  method: 'POST',
  body: JSON.stringify({ prompt }),
  signal: AbortSignal.timeout(tiers.task_creation), // ✅ 分级匹配
});

// ✅ 任务轮询：30s（代理场景兜底）
const pollResp = await fetchWithDiagnostics(`${baseUrl}/videos/${taskId}`, {
  signal: AbortSignal.timeout(tiers.task_polling), // ✅ 分级匹配
});

// ✅ 图像生成：60s（10-30s 常见）
const imageResp = await fetchWithDiagnostics(`${baseUrl}/images/generations`, {
  method: 'POST',
  body: JSON.stringify({ prompt: imagePrompt }),
  signal: AbortSignal.timeout(tiers.image_generation), // ✅ 分级匹配
});

// ✅ 视频下载：120s（大文件）
const videoResp = await fetchWithDiagnostics(videoUrl, {
  signal: AbortSignal.timeout(tiers.video_download), // ✅ 分级匹配
});

// ✅ LLM 调用：按 tokenBudget 分级
const llmTimeout = harnessConfig.budget.tokenBudget <= config.timeout_tier.llm_small_token_threshold
  ? tiers.llm_small : tiers.llm_large;
const harness = new Harness({ ...harnessConfig, timeout: llmTimeout }); // ✅

// ✅ 代理场景加宽超时
if (process.env.HTTPS_PROXY) {
  const proxyOverhead = config.timeout_tier.proxy_overhead_ms;
  const proxyResp = await fetchWithDiagnostics(url, {
    dispatcher: new ProxyAgent(process.env.HTTPS_PROXY),
    signal: AbortSignal.timeout(tiers.image_generation + proxyOverhead), // ✅ 80s
  });
}
```

## 错误示例

```typescript
// 错误 1：所有调用用同一超时值（BR-055-1 违规）
await fetch(url, { signal: AbortSignal.timeout(30000) }); // ❌ 视频下载需 120s
await fetch(url, { signal: AbortSignal.timeout(30000) }); // ❌ 任务创建只需 1s

// 错误 2：字面量硬编码超时值（BR-055-2 违规）
await fetch(url, { signal: AbortSignal.timeout(60000) }); // ❌ 应从 config 读取

// 错误 3：分级混用（BR-055-3 违规）
const createResp = await fetchWithDiagnostics(`${baseUrl}/videos`, {
  signal: AbortSignal.timeout(tiers.video_download), // ❌ 创建任务应秒级返回，用 120s 过长
});

// 错误 4：LLM 调用不按 tokenBudget 分级（BR-055-4 违规，suggestion）
const harness = new Harness({ timeout: 60000 }); // ❌ 16k token 需 180s

// 错误 5：代理场景未加宽超时（BR-055-5 违规，suggestion）
const resp = await fetchWithDiagnostics(url, {
  dispatcher: new ProxyAgent(process.env.HTTPS_PROXY),
  signal: AbortSignal.timeout(tiers.image_generation), // ❌ 代理增加 10-20s 延迟
});
```

## 适配新项目

- **OpenAI API 项目**：分级改为 chat_completion（60s） / embedding（30s） / image_generation（120s） / file_upload（300s）
- **AWS SDK 项目**：SDK 自带 retry + timeout 配置，本规则改为约束 SDK 配置项（`requestTimeout` / `httpOptions.timeout`）
- **gRPC 项目**：分级改为 unary_rpc（30s） / server_streaming（按业务） / client_streaming（按业务）
- **内部微服务项目**：统一超时 10s（同机房延迟低），但健康检查端点 5s（更快感知故障）
- **Python 项目**：`AbortSignal.timeout` 改为 `asyncio.wait_for`，`setTimeout` 改为 `threading.Timer`

## 与其他规则的关系

- 与 BR-054（外部 API 集成契约）联动：fetchWithDiagnostics 的 init.signal 必须按本规则分级设置
- 与 BR-057（长/短任务架构分离）联动：长任务的创建/轮询/下载三阶段分别用不同超时分级
- 与 BR-053（超时阈值链式匹配）联动：本规则是单层超时分级，BR-053 是多层调用链超时覆盖关系
- 与 BR-ASYNC-01（async 调用必须设置超时）联动：本规则细化了超时值的分级策略
- 与 CODING-057（超时分级策略）对应：本规则是 CODING-057 的后端审查视角
