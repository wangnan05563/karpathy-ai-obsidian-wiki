# 多源密钥解析审查规则（BR-056）

> 复盘来源：v3 媒体生成工具开发中，Agnes API key 可能配在三个位置：①`media.agnes.apiKey`（专用段，可选）②`llm.apiKeys.agnes`（共享段，config.json 已有）③环境变量（`media.agnes.apiKeyRef` 指向的变量名）。若只查一个位置会导致历史配置不兼容（用户已配在 llm.apiKeys.agnes，新增 media 段后找不到 key）（CODING-058）。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"多源密钥解析审查参数（api_key_resolution）"章节读取，禁止在本规则文件硬编码字段路径。

## Trigger Keywords

apiKey, apiKeyRef, apiKeys, dedicated, shared, env, fallback_chain, resolveApiKey, getEffectiveApiKey, process.env[, config.llm.apiKeys, config.media, 三级回退, 密钥解析, not configured

## Rules

### BR-056-1：密钥解析必须按"专用段 → 共享段 → 环境变量"三级回退

- **Severity**: critical
- **Description**: 调用需要 API Key 的外部服务时，密钥解析必须按 `api_key_resolution.fallback_chain`（默认 `['dedicated', 'shared', 'env']`）三级回退：①专用段 `config.<service>.apiKey` ②共享段 `config.llm.apiKeys.<provider>` ③环境变量 `process.env[config.<service>.apiKeyRef]`。只查一个位置会导致历史配置不兼容（用户已配在 llm.apiKeys.agnes，新增 media 段后找不到 key）。评审时确认：密钥解析函数实现了三级回退逻辑，禁止只查一个位置。
- **Suggested fix**:

```typescript
// 错误：只查专用段，不回退到共享段或环境变量
function resolveApiKey(mediaConfig: MediaConfig | undefined): string | null {
  if (!mediaConfig) return null;
  return mediaConfig.agnes.apiKey ?? null; // ❌ 历史配置在 llm.apiKeys.agnes 时找不到
}

// 正确：三级回退（专用段 → 共享段 → 环境变量）
function resolveAgnesApiKey(mediaConfig: MediaConfig | undefined, appConfig?: AppConfig): string | null {
  if (!mediaConfig) return null;
  // 第 1 级：专用段（media.agnes.apiKey）
  if (mediaConfig.agnes.apiKey) return mediaConfig.agnes.apiKey;
  // 第 2 级：共享段（llm.apiKeys.agnes）
  if (appConfig?.llm.apiKeys?.agnes) return appConfig.llm.apiKeys.agnes;
  // 第 3 级：环境变量（media.agnes.apiKeyRef 指向的变量名）
  const envKey = process.env[mediaConfig.agnes.apiKeyRef];
  if (envKey) return envKey;
  return null; // 全部缺失，由调用方抛错
}
```

### BR-056-2：回退顺序必须为"专用 → 共享 → 环境变量"，禁止调整

- **Severity**: critical
- **Description**: 回退顺序固定为"专用 → 共享 → 环境变量"，禁止调整。专用段优先级最高（服务专属配置，避免共享段密钥被误用）；环境变量优先级最低（部署环境兜底）。调整顺序会导致：环境变量优先于专用段时，专用段配置被忽略；共享段优先于专用段时，服务专属密钥被共享密钥覆盖。评审时确认：回退顺序与 `api_key_resolution.fallback_chain` 一致。
- **Suggested fix**:

```typescript
// 错误：回退顺序错误（环境变量优先于专用段）
function resolveApiKey(mediaConfig: MediaConfig | undefined): string | null {
  const envKey = process.env[mediaConfig.agnes.apiKeyRef];
  if (envKey) return envKey; // ❌ 环境变量优先级不应高于专用段
  return mediaConfig.agnes.apiKey ?? null;
}

// 正确：专用 → 共享 → 环境变量
function resolveApiKey(mediaConfig: MediaConfig | undefined, appConfig?: AppConfig): string | null {
  if (mediaConfig.agnes.apiKey) return mediaConfig.agnes.apiKey; // ✅ 专用段优先
  if (appConfig?.llm.apiKeys?.agnes) return appConfig.llm.apiKeys.agnes; // ✅ 共享段次之
  return process.env[mediaConfig.agnes.apiKeyRef] ?? null; // ✅ 环境变量最后
}
```

### BR-056-3：全部缺失时错误消息必须列出三个配置位置

- **Severity**: critical
- **Description**: 三级回退全部缺失时，错误消息必须按 `api_key_resolution.error_message_template` 模板列出三个配置位置（dedicated / shared / env），便于用户定位。未列出配置位置的错误消息（如 "API key not configured"）让用户不知道去哪配置。评审时确认：错误消息包含三个配置位置的具体字段路径。
- **Suggested fix**:

```typescript
// 错误：错误消息不列出配置位置，用户无法定位
if (!apiKey) {
  throw new Error('API key not configured'); // ❌ 未提示去哪配置
}

// 正确：错误消息列出三个配置位置
if (!apiKey) {
  throw new Error(
    `image generation: Agnes API key not configured ` +
    `(set media.agnes.apiKey or llm.apiKeys.agnes or env ${mediaConfig.agnes.apiKeyRef})` // ✅
  );
}
```

### BR-056-4：每级回退返回 null 时必须进入下一级，禁止返回 undefined 或空字符串

- **Severity**: suggestion
- **Description**: 每级回退返回 null 时必须进入下一级，禁止返回 undefined 或空字符串。undefined 和空字符串在后续逻辑中可能被误判为"有值"（如 `if (key)` 对空字符串返 false，但对 undefined 抛 TypeError）。统一返回 null 作为"未找到"语义，由调用方判断。评审时确认：每级回退的返回值为 null（非 undefined / 空字符串）。
- **Suggested fix**:

```typescript
// 错误：返回 undefined 或空字符串
function resolveApiKey(mediaConfig: MediaConfig | undefined): string | undefined {
  return mediaConfig?.agnes.apiKey; // ❌ 可能返回 undefined
}

// 正确：统一返回 null
function resolveApiKey(mediaConfig: MediaConfig | undefined): string | null {
  if (!mediaConfig) return null; // ✅
  if (mediaConfig.agnes.apiKey) return mediaConfig.agnes.apiKey;
  return null; // ✅ 统一 null 语义
}
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `api_key_resolution.enabled` | `true` | 是否启用本组规则（BR-056） |
| `api_key_resolution.severity_br056_1` | `critical` | BR-056-1 未实现三级回退违规严重级别 |
| `api_key_resolution.severity_br056_2` | `critical` | BR-056-2 回退顺序错误违规严重级别 |
| `api_key_resolution.severity_br056_3` | `critical` | BR-056-3 错误消息未列出配置位置违规严重级别 |
| `api_key_resolution.severity_br056_4` | `suggestion` | BR-056-4 返回值非 null 违规严重级别 |
| `api_key_resolution.fallback_chain` | `dedicated,shared,env` | 回退链路顺序数组 |
| `api_key_resolution.dedicated_field_pattern` | `config.{service}.apiKey` | 专用段字段路径模板 |
| `api_key_resolution.shared_field_pattern` | `config.llm.apiKeys.{provider}` | 共享段字段路径模板 |
| `api_key_resolution.env_ref_field_pattern` | `config.{service}.apiKeyRef` | 环境变量名字段路径模板 |
| `api_key_resolution.error_message_template` | 见下方 | 全部缺失时的错误消息模板 |
| `api_key_resolution.null_return_required` | `true` | 是否强制返回 null（非 undefined/空字符串） |

`error_message_template` 默认值：

```
{service} API key not configured (set {dedicated_field} or {shared_field} or env {env_ref_field})
```

## 检查方式

1. **三级回退检查**：用 Grep 检索密钥解析函数（`resolveApiKey` / `getEffectiveApiKey` 等），确认函数体内有三个配置位置的查询逻辑。只查一个位置 → **BR-056-1 违规**。
2. **顺序检查**：对三级回退函数，确认查询顺序为"专用段 → 共享段 → 环境变量"（专用段 if 在前，环境变量 if 在后）。顺序错误 → **BR-056-2 违规**。
3. **错误消息检查**：用 Grep 检索 `throw new Error` 中的 "not configured" 关键词，确认错误消息包含三个配置位置的字段路径。未列出 → **BR-056-3 违规**。
4. **返回值检查**：用 Grep 检索密钥解析函数的 return 语句，确认返回值为 null（非 undefined / 空字符串）。返回 undefined 或空字符串 → **BR-056-4 违规**（suggestion）。
5. **日志检查**：用 Grep 检索密钥解析函数中是否有 debug 级别日志记录命中哪一级回退。无日志 → suggestion（建议增加日志便于排查）。

## 正确示例

```typescript
// services/api/src/workflows/media-generation-workflow.ts
import type { MediaConfig, AppConfig } from '../types.js';

// 为什么三级回退：media 段可选，密钥可能只配在 llm.apiKeys.agnes（config.json 已有）或环境变量
function resolveAgnesApiKey(
  mediaConfig: MediaConfig | undefined,
  appConfig?: AppConfig,
): string | null {
  if (!mediaConfig) return null;

  // 第 1 级：专用段（media.agnes.apiKey）
  if (mediaConfig.agnes.apiKey) return mediaConfig.agnes.apiKey;

  // 第 2 级：共享段（llm.apiKeys.agnes）
  if (appConfig?.llm.apiKeys?.agnes) return appConfig.llm.apiKeys.agnes;

  // 第 3 级：环境变量（media.agnes.apiKeyRef 指向的变量名）
  const envKey = process.env[mediaConfig.agnes.apiKeyRef];
  if (envKey) return envKey;

  return null; // ✅ 统一返回 null
}

// 使用示例：调用方抛错时列出三个配置位置
export async function generateImage(...): Promise<{ url: string; alt: string; archivePath: string }> {
  const apiKey = resolveAgnesApiKey(mediaConfig, appConfig);
  if (!apiKey) {
    throw new Error(
      `image generation: Agnes API key not configured ` +
      `(set media.agnes.apiKey or llm.apiKeys.agnes or env ${mediaConfig.agnes.apiKeyRef})`, // ✅ 列出三个位置
    );
  }
  // ...
}
```

## 错误示例

```typescript
// 错误 1：只查专用段，不回退（BR-056-1 违规）
function resolveApiKey(mediaConfig: MediaConfig | undefined): string | null {
  if (!mediaConfig) return null;
  return mediaConfig.agnes.apiKey ?? null; // ❌ 历史配置在 llm.apiKeys.agnes 时找不到
}

// 错误 2：回退顺序错误（BR-056-2 违规）
function resolveApiKey(mediaConfig: MediaConfig | undefined): string | null {
  const envKey = process.env[mediaConfig.agnes.apiKeyRef];
  if (envKey) return envKey; // ❌ 环境变量优先级不应高于专用段
  return mediaConfig.agnes.apiKey ?? null;
}

// 错误 3：错误消息不列出配置位置（BR-056-3 违规）
if (!apiKey) {
  throw new Error('API key not configured'); // ❌ 未提示去哪配置
}

// 错误 4：返回 undefined（BR-056-4 违规，suggestion）
function resolveApiKey(mediaConfig: MediaConfig | undefined): string | undefined {
  return mediaConfig?.agnes.apiKey; // ❌ 可能返回 undefined
}

// 错误 5：返回空字符串（BR-056-4 违规，suggestion）
function resolveApiKey(mediaConfig: MediaConfig | undefined): string {
  return mediaConfig?.agnes.apiKey ?? ''; // ❌ 空字符串可能被误判
}
```

## 适配新项目

- **多 provider 项目**：`fallback_chain` 改为 `dedicated,shared,env,vault`，第 4 级从 HashiCorp Vault 读取
- **AWS Secrets Manager 项目**：第 4 级改为 AWS SDK 调用 `secretsmanager.getSecretValue`
- **Kubernetes Secret 项目**：环境变量从 K8s Secret 注入，`apiKeyRef` 字段指向 Secret key 名
- **多租户项目**：按租户 ID 查询专用段，回退到共享段时需校验租户权限
- **Python 项目**：`process.env[]` 改为 `os.environ.get()`，`config` 改为 `pydantic.BaseSettings`

## 与其他规则的关系

- 与 BR-054（外部 API 集成契约）联动：fetchWithDiagnostics 调用时 Authorization header 的 apiKey 必须按本规则三级回退解析
- 与 BR-035（敏感字段脱敏）联动：解析出的 apiKey 在日志中必须脱敏（仅显示前 4 位 + ***）
- 与 BR-037（跨 origin 持久化边界）联动：apiKey 必须存储在后端 config.json，前端 localStorage 禁止存储
- 与 BR-034（配置化参数检测）联动：apiKey 属于必须配置化的参数，禁止硬编码字面量
- 与 CODING-058（多源密钥解析）对应：本规则是 CODING-058 的后端审查视角
