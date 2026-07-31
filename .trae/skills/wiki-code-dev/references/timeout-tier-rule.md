# 超时分级策略规则（CODING-057）

> 复盘来源：v3 媒体生成工具开发中，视频创建任务、视频轮询、图像生成、视频下载、LLM 单轮调用五类操作的预估耗时差异巨大（秒级 → 分钟级），统一用一个超时值会导致：①短任务超时过长，失败时用户等待过久；②长任务超时过短，正常请求被误判超时。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `external_api.timeout_tiers` 字段读取，禁止在规则文件中硬编码超时毫秒数。

## 规则

**调用外部 API 或长任务时必须按预估耗时分级设置 `AbortSignal.timeout`，禁止所有调用用同一超时值**：

1. **任务创建**：`timeout_tiers.task_creation`（默认 30000ms / 30s），创建任务应秒级返回
2. **任务轮询**：`timeout_tiers.task_polling`（默认 30000ms / 30s），轮询应秒级返回，代理场景兜底
3. **图像生成**：`timeout_tiers.image_generation`（默认 60000ms / 60s），10-30s 常见，60s 兜底
4. **视频下载**：`timeout_tiers.video_download`（默认 120000ms / 120s），大文件下载
5. **LLM 单轮调用**：按 `token_budget` 调整，4k token → `timeout_tiers.llm_small`（默认 60000ms），16k token → `timeout_tiers.llm_large`（默认 180000ms）

## 适用场景

- 调用外部 API（图像/视频/LLM 等耗时差异大的服务）
- 长任务异步轮询（任务创建 + 状态轮询 + 结果下载三个阶段耗时不同）
- 通过代理访问外部服务（代理可能增加 10-20s 延迟，需放宽超时）
- LLM 调用按 tokenBudget 分级（4k / 8k / 16k / 32k 不同超时）

## 不适用场景

- 内部微服务调用（同机房网络延迟低，可统一超时）
- 同步函数调用（无网络 IO，无需超时）
- 浏览器端 fetch（浏览器有默认超时机制，且无法精确控制）
- 已有 SDK 自动管理超时的场景（SDK 内部已分级）

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `external_api.timeout_tiers.task_creation` | `30000` | 任务创建超时（毫秒） |
| `external_api.timeout_tiers.task_polling` | `30000` | 任务轮询超时（毫秒） |
| `external_api.timeout_tiers.image_generation` | `60000` | 图像生成超时（毫秒） |
| `external_api.timeout_tiers.video_download` | `120000` | 视频下载超时（毫秒） |
| `external_api.timeout_tiers.llm_small` | `60000` | LLM 小 token 预算超时（4k token） |
| `external_api.timeout_tiers.llm_large` | `180000` | LLM 大 token 预算超时（16k token） |
| `external_api.timeout_tiers.proxy_overhead_ms` | `20000` | 代理额外开销（毫秒），用于代理场景兜底加宽 |

## 检查方式

1. **分级配置检查**：config 中 `external_api.timeout_tiers` 必须含 6 个分级（task_creation / task_polling / image_generation / video_download / llm_small / llm_large）
2. **代码引用检查**：业务代码中 `AbortSignal.timeout(xxx)` 的 xxx 必须从 config 读取，禁止字面量硬编码
3. **分级匹配检查**：调用类型与超时分级必须匹配（创建任务用 task_creation，轮询用 task_polling，不可混用）
4. **代理场景检查**：通过 HTTPS_PROXY 访问外部 API 时，超时需考虑 `proxy_overhead_ms` 加宽
5. **LLM tokenBudget 检查**：LLM 调用按 tokenBudget 选择 llm_small 或 llm_large，禁止统一用一个值

## 正确示例

```typescript
// services/api/src/workflows/media-generation-workflow.ts
import { config } from '../config.js';

const tiers = config.external_api.timeout_tiers;

// ✅ 任务创建：30s（应秒级返回）
const createResp = await fetchWithDiagnostics(`${baseUrl}/videos`, {
  method: 'POST',
  body: JSON.stringify({ prompt }),
  signal: AbortSignal.timeout(tiers.task_creation),
});

// ✅ 任务轮询：30s（代理场景兜底）
const pollResp = await fetchWithDiagnostics(`${baseUrl}/videos/${taskId}`, {
  signal: AbortSignal.timeout(tiers.task_polling),
});

// ✅ 图像生成：60s（10-30s 常见）
const imageResp = await fetchWithDiagnostics(`${baseUrl}/images/generations`, {
  method: 'POST',
  body: JSON.stringify({ prompt: imagePrompt }),
  signal: AbortSignal.timeout(tiers.image_generation),
});

// ✅ 视频下载：120s（大文件）
const videoResp = await fetchWithDiagnostics(videoUrl, {
  signal: AbortSignal.timeout(tiers.video_download),
});

// ✅ LLM 调用：按 tokenBudget 分级
const llmTimeout = harnessConfig.budget.tokenBudget <= 4000 ? tiers.llm_small : tiers.llm_large;
const harness = new Harness({ ...harnessConfig, timeout: llmTimeout });
```

## 错误示例

```typescript
// ❌ 错误：所有调用用同一超时值（30s）
await fetch(url, { signal: AbortSignal.timeout(30000) }); // 视频下载需 120s，30s 会误判超时
await fetch(url, { signal: AbortSignal.timeout(30000) }); // 任务创建只需 1s，30s 失败时用户等待过久

// ❌ 错误：字面量硬编码超时值
await fetch(url, { signal: AbortSignal.timeout(60000) }); // ❌ 应从 config.external_api.timeout_tiers 读取

// ❌ 错误：LLM 调用不按 tokenBudget 分级
const harness = new Harness({ timeout: 60000 }); // ❌ 16k token 的 PPT 生成需 180s，60s 会超时
```

## 适配新项目

- 适配 OpenAI API：分级改为 chat_completion（60s） / embedding（30s） / image_generation（120s） / file_upload（300s）
- 适配 AWS SDK：SDK 自带 retry + timeout 配置，本规则改为约束 SDK 配置项（`requestTimeout` / `httpOptions.timeout`）
- 适配 gRPC：分级改为 unary_rpc（30s） / server_streaming（按业务） / client_streaming（按业务）
- 适配内部微服务：统一超时 10s（同机房延迟低），但健康检查端点 5s（更快感知故障）

## 与其他规则的关系

- 与 CODING-056（外部 API 集成契约）联动：fetchWithDiagnostics 的 init.signal 必须按本规则分级设置
- 与 CODING-059（长/短任务架构分离）联动：长任务的创建/轮询/下载三阶段分别用不同超时分级
- 与 CODING-025（Async 可靠性 - 多层超时防护）联动：本规则是网络层超时，与业务层超时（asyncio.wait_for / Promise.race）协同形成多层防护
- 与 CODING-013（优雅停止）联动：AbortSignal.timeout 触发中止时，fetchWithDiagnostics 抛 UND_ERR_ABORTED，需与 SIGINT/SIGTERM 触发的中止区分
