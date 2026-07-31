# 外部 API 集成契约规则（CODING-056）

> 复盘来源：v3 媒体生成工具开发中，Node.js 原生 fetch 调用 Agnes Image/Video API 时，网络层失败统一抛 `TypeError("fetch failed")`，真因藏在 `err.cause.code` 里；同时 Agnes Video API 的 Go 后端要求 `seconds` 字段为 string 类型（传 number 返 400），响应 URL 字段路径在 `data.url` 与 `data.metadata.url` 之间存在变更，需双重兼容。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `external_api` 字段读取，禁止在规则文件中硬编码错误码或提示文案。

## 规则

**调用第三方/外部 API 必须遵守四项契约**：

1. **fetchWithDiagnostics 包装**：禁止直接调用原生 `fetch`，必须用 `fetchWithDiagnostics` 包装，按 `err.cause.code` 分类翻译为可读诊断信息（网络超时 / DNS 失败 / 连接拒绝 / 证书错误 / 请求中止）。`fetchWithDiagnostics` 必须 export，便于单元测试直接验证错误转换逻辑，避免通过业务函数间接测试带来的 mock 复杂度。
2. **响应字段双重路径兼容**：外部 API 响应字段路径可能变更（如 `data.url` → `data.metadata.url`），消费方必须用 `data.url || data.metadata?.url` 双重兼容，避免 API 升级导致字段消失时业务失败。
3. **字段类型显式转换**：调用方后端语言要求的字段类型必须显式转换（如 Go 后端 string 类型用 `String(value)`），不能假设 JSON 序列化会自动适配。
4. **错误码分类**：`external_api.diagnostic_error_codes` 配置的错误码 → 提示文案映射表必须覆盖常见网络层错误（UND_ERR_CONNECT_TIMEOUT / ENOTFOUND / ECONNREFUSED / CERT_HAS_EXPIRED / UND_ERR_ABORTED）。

## 适用场景

- 调用第三方 / 外部 API（Agnes Image/Video API、OpenAI 兼容接口、GitHub API 等）
- 通过代理访问外部服务的场景（HTTPS_PROXY 环境变量 + undici ProxyAgent）
- 外部 API 响应字段路径不稳定，需多路径兼容的场景
- 外部 API 后端语言类型严格（Go / Rust 等），需显式类型转换的场景

## 不适用场景

- 内部微服务调用（同源、同语言、字段路径稳定）
- 浏览器端 fetch（浏览器 Fetch API 错误语义不同，本规则针对 Node.js undici fetch）
- 一次性临时脚本（无需长期维护，可简化错误处理）
- 已有 SDK 封装的 API（SDK 内部已处理错误转换）

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `external_api.diagnostic_error_codes` | 见下方映射表 | undici 错误码 → 可读提示文案映射 |
| `external_api.unknown_error_hint` | `cause?.message \|\| err.message` | 未匹配错误码时的兜底提示 |
| `external_api.export_for_testing` | `true` | fetchWithDiagnostics 必须 export 供单元测试 |
| `external_api.field_fallback_separator` | `\|\|` | 字段双重兼容操作符 |
| `external_api.type_conversion_required` | `true` | 是否强制类型显式转换 |

`diagnostic_error_codes` 默认映射表：

| 错误码 | 提示文案 |
|--------|---------|
| `UND_ERR_CONNECT_TIMEOUT` / `ETIMEDOUT` | 网络连接超时（{url} 不可达），请检查网络或代理设置 |
| `ENOTFOUND` | 域名解析失败（{hostname}），请检查 DNS 或网络连接 |
| `ECONNREFUSED` | 连接被拒绝（{host}），目标服务未启动或端口被防火墙拦截 |
| `CERT_HAS_EXPIRED` / `UNABLE_TO_VERIFY_LEAF_SIGNATURE` | TLS 证书校验失败（{code}），请检查系统时间或证书链 |
| `UND_ERR_ABORTED` | 请求超时或被中止，请确认目标服务响应是否过慢 |

## 检查方式

1. **fetchWithDiagnostics 包装检查**：Grep 搜索业务代码中的 `fetch(` 调用，必须全部替换为 `fetchWithDiagnostics(`（白名单：fetchWithDiagnostics 内部实现、测试 mock）
2. **错误码分类检查**：fetchWithDiagnostics 必须按 `external_api.diagnostic_error_codes` 映射表分类抛错，禁止直接 `throw err`
3. **字段双重兼容检查**：消费外部 API 响应时，关键业务字段必须用 `data.x || data.y?.x` 模式，禁止单路径访问
4. **类型显式转换检查**：调用 Go/Rust 后端 API 时，所有字段必须显式转换（`String()` / `Number()` / `Boolean()`）
5. **export 检查**：fetchWithDiagnostics 必须 `export async function`，便于单元测试直接 import

## 正确示例

```typescript
// services/api/src/workflows/media-generation-workflow.ts
// 为什么 export：单元测试需直接验证错误转换逻辑，避免通过 generateImage 间接测试带来的 Harness mock 复杂度
export async function fetchWithDiagnostics(url: string, init: RequestInit): Promise<Response> {
  try {
    return await fetch(url, init);
  } catch (err) {
    const cause = (err as { cause?: { code?: string; message?: string } }).cause;
    const code = cause?.code;
    const hints = config.external_api.diagnostic_error_codes;
    let hint: string;
    if (code === 'UND_ERR_CONNECT_TIMEOUT' || code === 'ETIMEDOUT') {
      hint = `网络连接超时（${url} 不可达），请检查网络或代理设置`;
    } else if (code === 'ENOTFOUND') {
      hint = `域名解析失败（${new URL(url).hostname}），请检查 DNS 或网络连接`;
    } else if (code === 'ECONNREFUSED') {
      hint = `连接被拒绝（${new URL(url).host}），目标服务未启动或端口被防火墙拦截`;
    } else {
      hint = cause?.message || (err instanceof Error ? err.message : String(err));
    }
    throw new Error(`请求 ${url} 失败：${hint}（${code || 'unknown'}）`);
  }
}

// ✅ 调用外部 API：用 fetchWithDiagnostics 包装 + 字段双重兼容 + 类型显式转换
const response = await fetchWithDiagnostics(`${mediaConfig.agnes.baseUrl}/videos`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
  body: JSON.stringify({
    model: mediaConfig.agnes.videoModel,
    prompt,
    seconds: String(mediaConfig.agnes.defaultVideoSeconds), // ✅ Go 后端要求 string 类型
  }),
  signal: AbortSignal.timeout(config.external_api.timeout_tiers.task_creation),
});

// ✅ 响应字段双重路径兼容
const data = await response.json();
const videoUrl = data.url || data.metadata?.url; // ✅ 兼容字段路径变更
```

## 错误示例

```typescript
// ❌ 错误：直接用原生 fetch，错误信息不可读
const response = await fetch('https://api.agnes.com/videos', {
  method: 'POST',
  body: JSON.stringify({ seconds: 60 }), // ❌ Go 后端要求 string，传 number 返 400
});
// 网络失败时只抛 TypeError("fetch failed")，真因藏在 err.cause.code 里

// ❌ 错误：单路径访问响应字段，API 升级时业务中断
const data = await response.json();
const videoUrl = data.url; // ❌ API 改字段路径为 data.metadata.url 时直接 undefined

// ❌ 错误：fetchWithDiagnostics 未 export，单元测试只能通过业务函数间接测试
async function fetchWithDiagnostics(url: string, init: RequestInit) { ... } // ❌ 缺少 export
```

## 适配新项目

- 适配 Axios：将 fetchWithDiagnostics 改为 axiosWithDiagnostics，错误码映射从 `err.code`（Axios 错误）读取，`ERR_NETWORK` / `ECONNABORTED` / `ETIMEDOUT` 等
- 适配浏览器端 fetch：浏览器 Fetch API 错误无 `cause.code`，需从 `err.message` 模式匹配（"Failed to fetch" / "NetworkError"）
- 适配 gRPC：错误码从 `err.code`（gRPC status code）读取，映射表覆盖 UNAVAILABLE / DEADLINE_EXCEEDED / UNAUTHENTICATED 等
- 适配 GraphQL：错误从 `errors[]` 数组读取，每个 error 含 `extensions.code` 字段

## 与其他规则的关系

- 与 CODING-057（超时分级策略）联动：fetchWithDiagnostics 的 init 参数中 `signal: AbortSignal.timeout(xxx)` 必须按超时分级配置
- 与 CODING-058（多源密钥解析）联动：fetchWithDiagnostics 调用时 Authorization header 的 apiKey 必须按三级回退解析
- 与 CODING-059（长/短任务架构分离）联动：长任务端点必须用 fetchWithDiagnostics 包装创建/轮询调用
- 与 CODING-013（优雅停止）联动：fetchWithDiagnostics 中止时（UND_ERR_ABORTED）的提示文案需与优雅停止信号区分
