# 外部 API 集成契约审查规则（BR-054）

> 复盘来源：v3 媒体生成工具开发中，Node.js 原生 fetch 调用 Agnes Image/Video API 时，网络层失败统一抛 `TypeError("fetch failed")`，真因藏在 `err.cause.code` 里；同时 Agnes Video API 的 Go 后端要求 `seconds` 字段为 string 类型（传 number 返 400），响应 URL 字段路径在 `data.url` 与 `data.metadata.url` 之间存在变更，需双重兼容（CODING-056）。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"外部 API 集成契约审查参数（external_api_contract）"章节读取，禁止在本规则文件硬编码错误码或提示文案。

## Trigger Keywords

fetch(, fetchWithDiagnostics, err.cause.code, UND_ERR_CONNECT_TIMEOUT, ENOTFOUND, ECONNREFUSED, CERT_HAS_EXPIRED, UND_ERR_ABORTED, data.url, data.metadata.url, String(value), Number(value), Boolean(value), Go 后端, type conversion, field fallback, 双重兼容, undici, ProxyAgent

## Rules

### BR-054-1：调用外部 API 必须用 fetchWithDiagnostics 包装，禁止直接用原生 fetch

- **Severity**: critical
- **Description**: 业务代码中调用第三方/外部 API 必须用 `fetchWithDiagnostics` 包装原生 `fetch`，按 `external_api_contract.diagnostic_error_codes` 映射表将 `err.cause.code` 分类翻译为可读诊断信息（网络超时 / DNS 失败 / 连接拒绝 / 证书错误 / 请求中止）。原生 fetch 网络失败时只抛 `TypeError("fetch failed")`，真因藏在 `err.cause.code` 里，用户无法定位是网络问题还是服务问题。`fetchWithDiagnostics` 必须 `export`，便于单元测试直接验证错误转换逻辑，避免通过业务函数间接测试带来的 mock 复杂度。评审时确认：业务代码中无直接 `fetch(` 调用（白名单：fetchWithDiagnostics 内部实现、测试 mock、Node.js 内置模块）。
- **Suggested fix**:

```typescript
// 错误：直接用原生 fetch，网络失败时只抛 TypeError("fetch failed")
const response = await fetch('https://api.agnes.com/videos', {
  method: 'POST',
  body: JSON.stringify({ prompt }),
});
// ❌ 网络失败时 err.message = "fetch failed"，真因藏在 err.cause.code 里

// 正确：用 fetchWithDiagnostics 包装，错误码分类翻译
export async function fetchWithDiagnostics(url: string, init: RequestInit): Promise<Response> {
  try {
    return await fetch(url, init);
  } catch (err) {
    const cause = (err as { cause?: { code?: string; message?: string } }).cause;
    const code = cause?.code;
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

// 业务代码调用
const response = await fetchWithDiagnostics(`${baseUrl}/videos`, { method: 'POST', ... });
```

### BR-054-2：响应字段必须双重路径兼容，禁止单路径访问

- **Severity**: critical
- **Description**: 外部 API 响应字段路径可能变更（如 `data.url` → `data.metadata.url`），消费方必须用 `external_api_contract.field_fallback_separator`（默认 `||`）做双重路径兼容（`data.url || data.metadata?.url`）。单路径访问在外部 API 升级字段路径时会直接返回 undefined 导致业务中断。评审时确认：外部 API 响应的关键业务字段（URL / ID / 文件路径等）均用双重路径兼容模式访问。
- **Suggested fix**:

```typescript
// 错误：单路径访问，API 升级字段路径时直接 undefined
const data = await response.json();
const videoUrl = data.url; // ❌ API 改字段路径为 data.metadata.url 时直接 undefined

// 正确：双重路径兼容
const videoUrl = data.url || data.metadata?.url; // ✅ 兼容字段路径变更
```

### BR-054-3：调用方后端语言要求的字段类型必须显式转换

- **Severity**: critical
- **Description**: 调用外部 API 时，若调用方后端语言（如 Go / Rust）对字段类型严格，必须显式转换字段类型（如 Go 后端 string 类型用 `String(value)`，number 类型用 `Number(value)`）。JSON 序列化不会自动适配语言差异，Go 后端 `json.Unmarshal` 遇到类型不匹配会返 400。`external_api_contract.type_conversion_required`（默认 `true`）启用时，所有传给 Go/Rust 后端的字段必须显式转换。评审时确认：调用 Go/Rust 后端 API 的请求体中，number/boolean 字段已用 `String()` / `Number()` / `Boolean()` 显式转换。
- **Suggested fix**:

```typescript
// 错误：Go 后端要求 seconds 为 string，传 number 返 400
body: JSON.stringify({
  model: videoModel,
  prompt,
  seconds: 60, // ❌ Go 后端 json.Unmarshal 失败，返 400
})

// 正确：显式转换为 string
body: JSON.stringify({
  model: videoModel,
  prompt,
  seconds: String(60), // ✅ Go 后端接受 string 类型
})
```

### BR-054-4：fetchWithDiagnostics 必须 export 供单元测试

- **Severity**: suggestion
- **Description**: `fetchWithDiagnostics` 必须 `export async function`，便于单元测试直接 import 验证错误转换逻辑。未 export 时单元测试只能通过业务函数间接测试，需 mock Harness 等复杂依赖，测试维护成本高。`external_api_contract.export_for_testing`（默认 `true`）启用时，fetchWithDiagnostics 必须 export。评审时确认：fetchWithDiagnostics 声明前有 `export` 关键字。
- **Suggested fix**:

```typescript
// 错误：fetchWithDiagnostics 未 export，单元测试只能间接测试
async function fetchWithDiagnostics(url: string, init: RequestInit) { ... } // ❌ 缺少 export

// 正确：export 供单元测试直接 import
export async function fetchWithDiagnostics(url: string, init: RequestInit) { ... } // ✅
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `external_api_contract.enabled` | `true` | 是否启用本组规则（BR-054） |
| `external_api_contract.severity_br054_1` | `critical` | BR-054-1 直接用原生 fetch 违规严重级别 |
| `external_api_contract.severity_br054_2` | `critical` | BR-054-2 单路径访问违规严重级别 |
| `external_api_contract.severity_br054_3` | `critical` | BR-054-3 类型未显式转换违规严重级别 |
| `external_api_contract.severity_br054_4` | `suggestion` | BR-054-4 未 export 违规严重级别 |
| `external_api_contract.diagnostic_error_codes` | 见下方映射表 | undici 错误码 → 可读提示文案映射 |
| `external_api_contract.unknown_error_hint` | `cause?.message \|\| err.message` | 未匹配错误码时的兜底提示 |
| `external_api_contract.export_for_testing` | `true` | fetchWithDiagnostics 必须 export 供单元测试 |
| `external_api_contract.field_fallback_separator` | `\|\|` | 字段双重兼容操作符 |
| `external_api_contract.type_conversion_required` | `true` | 是否强制类型显式转换 |
| `external_api_contract.fetch_whitelist` | `fetchWithDiagnostics internal,test mock` | 允许直接用 fetch 的白名单 |

`diagnostic_error_codes` 默认映射表：

| 错误码 | 提示文案 |
|--------|---------|
| `UND_ERR_CONNECT_TIMEOUT` / `ETIMEDOUT` | 网络连接超时（{url} 不可达），请检查网络或代理设置 |
| `ENOTFOUND` | 域名解析失败（{hostname}），请检查 DNS 或网络连接 |
| `ECONNREFUSED` | 连接被拒绝（{host}），目标服务未启动或端口被防火墙拦截 |
| `CERT_HAS_EXPIRED` / `UNABLE_TO_VERIFY_LEAF_SIGNATURE` | TLS 证书校验失败（{code}），请检查系统时间或证书链 |
| `UND_ERR_ABORTED` | 请求超时或被中止，请确认目标服务响应是否过慢 |

## 检查方式

1. **fetchWithDiagnostics 包装检查**：用 Grep 在 `api/src/` 目录检索 `fetch(` 调用，逐个确认是否为 fetchWithDiagnostics 内部实现或测试 mock（白名单）。业务代码中的直接 `fetch(` 调用 → **BR-054-1 违规**。
2. **错误码分类检查**：用 Grep 检索 `fetchWithDiagnostics` 实现体，确认是否按 `diagnostic_error_codes` 映射表分类抛错。直接 `throw err` 无分类 → **BR-054-1 违规**（错误信息不可读）。
3. **字段双重兼容检查**：用 Grep 检索外部 API 响应消费代码（`await response.json()` 后的字段访问），关键业务字段（URL / ID / 文件路径）必须用 `data.x || data.y?.x` 模式。单路径访问 → **BR-054-2 违规**。
4. **类型显式转换检查**：用 Grep 检索调用 Go/Rust 后端 API 的请求体构造代码，number/boolean 字段必须用 `String()` / `Number()` / `Boolean()` 显式转换。未转换 → **BR-054-3 违规**。
5. **export 检查**：用 Grep 检索 `fetchWithDiagnostics` 声明，确认前有 `export` 关键字。未 export → **BR-054-4 违规**（suggestion）。

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
  signal: AbortSignal.timeout(config.external_api_contract.timeout_tiers.task_creation),
});

// ✅ 响应字段双重路径兼容
const data = await response.json();
const videoUrl = data.url || data.metadata?.url; // ✅ 兼容字段路径变更
```

## 错误示例

```typescript
// 错误 1：直接用原生 fetch，错误信息不可读（BR-054-1 违规）
const response = await fetch('https://api.agnes.com/videos', {
  method: 'POST',
  body: JSON.stringify({ seconds: 60 }), // ❌ Go 后端要求 string，传 number 返 400
});
// 网络失败时只抛 TypeError("fetch failed")，真因藏在 err.cause.code 里

// 错误 2：单路径访问响应字段，API 升级时业务中断（BR-054-2 违规）
const data = await response.json();
const videoUrl = data.url; // ❌ API 改字段路径为 data.metadata.url 时直接 undefined

// 错误 3：未显式转换类型，Go 后端返 400（BR-054-3 违规）
body: JSON.stringify({
  seconds: 60, // ❌ Go 后端 json.Unmarshal 失败
  enabled: true, // ❌ Go 后端可能要求 string "true"
})

// 错误 4：fetchWithDiagnostics 未 export（BR-054-4 违规，suggestion）
async function fetchWithDiagnostics(url: string, init: RequestInit) { ... } // ❌ 缺少 export

// 错误 5：fetchWithDiagnostics 直接 throw err 无分类（BR-054-1 违规）
export async function fetchWithDiagnostics(url: string, init: RequestInit) {
  try { return await fetch(url, init); }
  catch (err) { throw err; } // ❌ 未按 err.cause.code 分类翻译
}
```

## 适配新项目

- **Axios 项目**：将 fetchWithDiagnostics 改为 axiosWithDiagnostics，错误码映射从 `err.code`（Axios 错误）读取，覆盖 `ERR_NETWORK` / `ECONNABORTED` / `ETIMEDOUT` 等
- **浏览器端 fetch**：浏览器 Fetch API 错误无 `cause.code`，需从 `err.message` 模式匹配（"Failed to fetch" / "NetworkError"）
- **gRPC 项目**：错误码从 `err.code`（gRPC status code）读取，映射表覆盖 UNAVAILABLE / DEADLINE_EXCEEDED / UNAUTHENTICATED 等
- **GraphQL 项目**：错误从 `errors[]` 数组读取，每个 error 含 `extensions.code` 字段
- **Python httpx/aiohttp**：错误码从 `err.__class__.__name__` 读取，映射表覆盖 ConnectTimeout / ClientConnectorError 等

## 与其他规则的关系

- 与 BR-055（超时分级策略）联动：fetchWithDiagnostics 的 init 参数中 `signal: AbortSignal.timeout(xxx)` 必须按超时分级配置
- 与 BR-056（多源密钥解析）联动：fetchWithDiagnostics 调用时 Authorization header 的 apiKey 必须按三级回退解析
- 与 BR-057（长/短任务架构分离）联动：长任务端点必须用 fetchWithDiagnostics 包装创建/轮询调用
- 与 BR-035（敏感字段脱敏）联动：fetchWithDiagnostics 抛出的错误消息中不得包含 apiKey 等敏感信息
- 与 CODING-056（外部 API 集成契约）对应：本规则是 CODING-056 的后端审查视角
