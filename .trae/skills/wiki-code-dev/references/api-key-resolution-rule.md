# 多源密钥解析规则（CODING-058）

> 复盘来源：v3 媒体生成工具开发中，Agnes API key 可能配在三个位置：①`media.agnes.apiKey`（专用段，可选）②`llm.apiKeys.agnes`（共享段，config.json 已有）③环境变量（`media.agnes.apiKeyRef` 指向的变量名）。若只查一个位置会导致历史配置不兼容（用户已配在 llm.apiKeys.agnes，新增 media 段后找不到 key）。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `api_key_resolution` 字段读取，禁止在规则文件中硬编码字段路径。

## 规则

**调用需要 API Key 的外部服务时，密钥解析必须按"专用段 → 共享段 → 环境变量"三级回退**：

1. **专用段**：`config.<service>.apiKey`（如 `media.agnes.apiKey`），服务专属配置
2. **共享段**：`config.llm.apiKeys.<provider>`（如 `llm.apiKeys.agnes`），多服务共享的 provider 密钥
3. **环境变量**：`process.env[config.<service>.apiKeyRef]`，部署环境注入的密钥
4. **全部缺失时抛错**：错误消息必须列出三个配置位置，便于用户定位

回退顺序固定为"专用 → 共享 → 环境变量"，禁止调整顺序（专用段优先级最高，避免共享段密钥被误用）。

## 适用场景

- 调用需要 API Key 的外部服务（Agnes / OpenAI / Anthropic / Azure 等）
- 一个 provider 密钥被多个服务共用的场景（如 Agnes 同时提供图像/视频/LLM 服务）
- 历史配置迁移场景（用户已配在 llm.apiKeys，新增 media 段后无需重新配置）
- 多环境部署（开发环境用 .env，生产环境用 config.json，CI/CD 用环境变量）

## 不适用场景

- 无需 API Key 的公开 API（如 GitHub 公开仓库 API）
- 内部微服务调用（用服务间认证，非 API Key 模式）
- 浏览器端调用（API Key 不应暴露在前端，本规则针对后端）
- 一次性临时脚本（可直接从环境变量读取，无需多源回退）

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `api_key_resolution.fallback_chain` | `['dedicated', 'shared', 'env']` | 回退链路顺序数组 |
| `api_key_resolution.dedicated_field_pattern` | `config.{service}.apiKey` | 专用段字段路径模板 |
| `api_key_resolution.shared_field_pattern` | `config.llm.apiKeys.{provider}` | 共享段字段路径模板 |
| `api_key_resolution.env_ref_field_pattern` | `config.{service}.apiKeyRef` | 环境变量名字段路径模板 |
| `api_key_resolution.error_message_template` | 见下方 | 全部缺失时的错误消息模板 |

`error_message_template` 默认值：

```
{service} API key not configured (set {dedicated_field} or {shared_field} or env {env_ref_field})
```

## 检查方式

1. **三级回退检查**：密钥解析函数必须实现三级回退，禁止只查一个位置
2. **顺序检查**：回退顺序必须为"专用 → 共享 → 环境变量"，禁止调整（用 `fallback_chain` 配置控制）
3. **错误消息检查**：全部缺失时的错误消息必须列出三个配置位置（dedicated / shared / env）
4. **null 检查**：每级回退返回 null 时必须进入下一级，禁止返回 undefined 或空字符串
5. **日志检查**：命中哪一级回退必须记录日志（debug 级别），便于排查配置问题

## 正确示例

```typescript
// services/api/src/workflows/media-generation-workflow.ts
import type { MediaConfig, AppConfig } from '../types.js';
import { config } from '../config.js';

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

  return null; // 全部缺失，由调用方抛错
}

// 使用示例：调用方抛错时列出三个配置位置
export async function generateImage(...): Promise<{ url: string; alt: string; archivePath: string }> {
  const apiKey = resolveAgnesApiKey(mediaConfig, appConfig);
  if (!apiKey) {
    throw new Error(
      `image generation: Agnes API key not configured ` +
      `(set media.agnes.apiKey or llm.apiKeys.agnes or env ${mediaConfig.agnes.apiKeyRef})`,
    );
  }
  // ...
}
```

## 错误示例

```typescript
// ❌ 错误：只查专用段，不回退到共享段或环境变量
function resolveApiKey(mediaConfig: MediaConfig | undefined): string | null {
  if (!mediaConfig) return null;
  return mediaConfig.agnes.apiKey ?? null; // ❌ 历史配置在 llm.apiKeys.agnes 时找不到
}

// ❌ 错误：回退顺序错误（环境变量优先于专用段）
function resolveApiKey(mediaConfig: MediaConfig | undefined): string | null {
  const envKey = process.env[mediaConfig.agnes.apiKeyRef];
  if (envKey) return envKey; // ❌ 环境变量优先级不应高于专用段
  return mediaConfig.agnes.apiKey ?? null;
}

// ❌ 错误：错误消息不列出配置位置，用户无法定位
if (!apiKey) {
  throw new Error('API key not configured'); // ❌ 未提示去哪配置
}
```

## 适配新项目

- 适配多 provider：`fallback_chain` 改为 `['dedicated', 'shared', 'env', 'vault']`，第 4 级从 HashiCorp Vault 读取
- 适配 AWS Secrets Manager：第 4 级改为 AWS SDK 调用 `secretsmanager.getSecretValue`
- 适配 Kubernetes Secret：环境变量从 K8s Secret 注入，`apiKeyRef` 字段指向 Secret key 名
- 适配多租户：按租户 ID 查询专用段，回退到共享段时需校验租户权限

## 与其他规则的关系

- 与 CODING-056（外部 API 集成契约）联动：fetchWithDiagnostics 调用时 Authorization header 的 apiKey 必须按本规则三级回退解析
- 与 CODING-014（敏感字段脱敏）联动：解析出的 apiKey 在日志中必须脱敏（仅显示前 4 位 + ***）
- 与 CODING-037（跨 origin 持久化边界）联动：apiKey 必须存储在后端 config.json，前端 localStorage 禁止存储
- 与 CODING-007（配置化无硬编码）联动：回退字段路径从 `api_key_resolution.fallback_chain` 读取，禁止硬编码
